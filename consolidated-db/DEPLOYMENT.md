# Healthbridge Care+ Consolidated Database - Deployment Guide

## Prerequisites

### Required on AI1/AI2 Servers
- Ubuntu 22.04 LTS or newer
- Docker Engine 20.10+
- Docker Compose 2.0+
- Minimum 8GB RAM
- Minimum 50GB disk space
- Network access to:
  - Central Registry (clumiddle.aodv.local)
  - BOF API (bof.asst-brianza.it)
  - Aurora DB (10.30.208.195:1521)

### Required Credentials
- PostgreSQL database password (create new secure password)
- API token for unified endpoint (create new secure token)
- Aurora Oracle credentials: `PROG_PILI / PwdProgPili01`
- BOF API token: `bof-0fb7a45b-41e4-4a85-820b-1b82a7775739`

---

## Step 1: Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Log out and back in for group changes to take effect
```

---

## Step 2: Transfer Files to Server

```bash
# On your local machine, from project root
cd /home/admin1/Live_Projects/Healthcare-Bridge-Demo/healthcare-bridge-demo

# Create tarball
tar -czf consolidated-db.tar.gz consolidated-db/

# Transfer to AI1 (replace with actual SSH credentials)
scp consolidated-db.tar.gz user@10.30.229.21:/home/user/

# SSH into AI1
ssh user@10.30.229.21

# Extract files
cd /home/user
tar -xzf consolidated-db.tar.gz
cd consolidated-db
```

---

## Step 3: Configure Environment Variables

```bash
# Navigate to docker directory
cd docker/

# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Configure the following:**

```bash
# PostgreSQL Database Configuration
DB_NAME=healthbridge_care
DB_USER=healthbridge_user
DB_PASSWORD=YOUR_SECURE_PASSWORD_HERE  # Generate strong password (16+ chars)

# API Configuration
API_TOKEN=YOUR_SECURE_API_TOKEN_HERE  # Generate secure token (32+ chars)

# Data Source Configuration (verify URLs are correct)
REGISTRY_API_URL=https://clumiddle.aodv.local/AC/pac/rest/paziente

# Aurora Oracle Database
AURORA_HOST=10.30.208.195
AURORA_USER=PROG_PILI
AURORA_PASSWORD=PwdProgPili01

# BOF API
BOF_API_URL=https://bof.asst-brianza.it/api/v1/index.php
BOF_API_TOKEN=bof-0fb7a45b-41e4-4a85-820b-1b82a7775739
```

**Generate secure passwords:**
```bash
# Generate secure database password
openssl rand -base64 24

# Generate secure API token
openssl rand -hex 32
```

---

## Step 4: Deploy Services

```bash
# Make sure you're in the docker/ directory
cd /home/user/consolidated-db/docker/

# Start services (detached mode)
docker-compose up -d

# Check service status
docker-compose ps

# Expected output:
# NAME                     STATUS              PORTS
# healthbridge_postgres    Up (healthy)        0.0.0.0:5432->5432/tcp
# healthbridge_api         Up (healthy)        0.0.0.0:8080->8080/tcp
# healthbridge_etl         Up                  -

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f etl
docker-compose logs -f postgres
```

---

## Step 5: Verify Deployment

### Test Database Connection

```bash
# Connect to PostgreSQL container
docker exec -it healthbridge_postgres psql -U healthbridge_user -d healthbridge_care

# Run test queries
SELECT version();
SELECT * FROM etl_metadata;
\dt  # List tables
\q   # Quit
```

### Test API Endpoint

```bash
# Health check
curl http://localhost:8080/status

# Expected response:
# {"status":"healthy","database":"connected","timestamp":"..."}

# Test patient endpoint (replace TOKEN with your API_TOKEN)
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     http://localhost:8080/api/v1/patient/RSSMRA85M01F205X

# Test ETL status
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     http://localhost:8080/api/v1/etl/status
```

### Verify ETL Jobs

```bash
# Check ETL logs
docker-compose logs etl

# Manually trigger ETL run
docker exec -it healthbridge_etl python run_etl.py

# Check database for loaded data
docker exec -it healthbridge_postgres psql -U healthbridge_user -d healthbridge_care \
  -c "SELECT COUNT(*) FROM patients;"
```

---

## Step 6: Configure Firewall

```bash
# Allow API port (8080) from AWS VPC subnet
sudo ufw allow from 172.31.0.0/16 to any port 8080 proto tcp

# Check firewall status
sudo ufw status
```

---

## Step 7: Configure AWS Application

Update AWS backend to use the new consolidated API endpoint:

```bash
# On AWS EC2 (35.157.93.232)
ssh -i ~/.ssh/healthcare-bridge.pem ubuntu@35.157.93.232

# Edit backend .env file
nano /path/to/backend/.env

# Add/update:
CONSOLIDATED_API_URL=http://10.30.229.21:8080
CONSOLIDATED_API_TOKEN=YOUR_API_TOKEN

# Restart backend
docker-compose restart backend
```

---

## Monitoring and Maintenance

### View Service Status

```bash
docker-compose ps
docker-compose logs -f
```

### Check Database Size

```bash
docker exec -it healthbridge_postgres psql -U healthbridge_user -d healthbridge_care \
  -c "SELECT pg_size_pretty(pg_database_size('healthbridge_care'));"
```

### Check ETL Status

```bash
docker exec -it healthbridge_postgres psql -U healthbridge_user -d healthbridge_care \
  -c "SELECT * FROM etl_metadata;"
```

### View API Logs

```bash
docker-compose logs -f api | grep ERROR
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
docker-compose restart etl
```

### Stop Services

```bash
docker-compose stop    # Stop without removing containers
docker-compose down    # Stop and remove containers (data persists in volumes)
```

---

## Backup and Recovery

### Backup Database

```bash
# Create backup directory
mkdir -p /home/user/backups

# Backup database
docker exec healthbridge_postgres pg_dump -U healthbridge_user healthbridge_care > \
  /home/user/backups/healthbridge_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker exec healthbridge_postgres pg_dump -U healthbridge_user healthbridge_care | \
  gzip > /home/user/backups/healthbridge_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore Database

```bash
# Stop ETL service first
docker-compose stop etl

# Restore from backup
cat /home/user/backups/healthbridge_20250216_120000.sql | \
  docker exec -i healthbridge_postgres psql -U healthbridge_user healthbridge_care

# Or restore from compressed backup
gunzip -c /home/user/backups/healthbridge_20250216_120000.sql.gz | \
  docker exec -i healthbridge_postgres psql -U healthbridge_user healthbridge_care

# Restart ETL
docker-compose start etl
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Check if PostgreSQL is accepting connections
docker exec healthbridge_postgres pg_isready -U healthbridge_user

# Test connection from host
psql -h localhost -U healthbridge_user -d healthbridge_care
```

### API Not Responding

```bash
# Check API logs
docker-compose logs api

# Check if API port is listening
netstat -tulpn | grep 8080

# Restart API service
docker-compose restart api
```

### ETL Failures

```bash
# Check ETL logs
docker-compose logs etl

# Check data source connectivity
docker exec -it healthbridge_etl python << EOF
import cx_Oracle
dsn = cx_Oracle.makedsn("10.30.208.195", 1521, service_name="E4CURE")
conn = cx_Oracle.connect(user="PROG_PILI", password="PwdProgPili01", dsn=dsn)
print("Aurora connection successful!")
conn.close()
EOF

# Manually run ETL
docker exec -it healthbridge_etl python run_etl.py
```

### Disk Space Issues

```bash
# Check disk usage
df -h

# Check Docker volume sizes
docker system df -v

# Clean up old logs
docker-compose logs --tail=1000 api > /dev/null
docker-compose logs --tail=1000 etl > /dev/null

# Prune unused Docker resources (careful!)
docker system prune -a
```

---

## Performance Tuning

### PostgreSQL Optimization

```bash
# Edit PostgreSQL config (inside container)
docker exec -it healthbridge_postgres bash
vi /var/lib/postgresql/data/postgresql.conf

# Recommended settings for 8GB RAM:
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB

# Restart PostgreSQL
docker-compose restart postgres
```

### ETL Schedule Adjustment

Edit `consolidated-db/etl/scheduler.py` to change ETL frequency:

```python
# Change from every 15 minutes to every 30 minutes
schedule.every(30).minutes.do(run_etl_job)
```

Then rebuild and restart:
```bash
docker-compose up -d --build etl
```

---

## Security Checklist

- [ ] Strong database password (16+ characters)
- [ ] Secure API token (32+ characters)
- [ ] Firewall configured (only allow AWS VPC subnet)
- [ ] TLS/SSL enabled for API (add nginx reverse proxy)
- [ ] Database backups automated
- [ ] Log rotation configured
- [ ] Non-root users in containers
- [ ] Secrets not committed to version control

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review troubleshooting section above
3. Contact development team

---

## Next Steps

After successful deployment:

1. ✅ Verify all ETL jobs running successfully
2. ✅ Test API endpoint from AWS EC2
3. ✅ Update AWS backend to use consolidated API
4. ✅ Configure VPN routing to include 10.30.229.16/29 subnet
5. ✅ Perform end-to-end test with real patient data
6. ✅ Set up automated backups
7. ✅ Configure monitoring and alerts
