# Healthbridge Care+ Consolidated Database System

This directory contains the consolidated database architecture for deployment on ASST-AI1/AI2 servers.

## Directory Structure

```
consolidated-db/
├── schema/           # PostgreSQL database schema
├── etl/             # ETL scripts for data extraction
├── api/             # Unified FastAPI endpoint
├── docker/          # Docker Compose configuration
└── README.md        # This file
```

## Architecture Overview

### Data Flow
1. **Central Registry** (clumiddle.aodv.local) → Patient validation & demographics
2. **Aurora DB** (10.30.208.195:1521) → Clinical events timeline
3. **BOF API** (bof.asst-brianza.it) → Protected discharges & care continuity
4. **ETL Process** → Consolidated PostgreSQL database
5. **Unified API** → Single endpoint for AWS application

### Database Tables

#### `patients` (Primary)
- Source: Central Patient Registry
- Primary Key: `fiscal_code` (Italian fiscal code)
- Contains: Demographics, exemptions, disability status, caregiver info

#### `clinical_events`
- Source: Aurora DB (PAZIENTI_ACCESSO2 view)
- Contains: ED visits, hospitalizations, outpatient visits, therapies, allergies

#### `protected_discharges`
- Source: BOF API
- Contains: Discharge plans, home care, palliative care, SGDT visits

#### `etl_metadata`
- Tracks ETL job runs, data freshness, sync status

## Setup Instructions

### 1. Database Installation (on AI1/AI2)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE healthbridge_care;
CREATE USER healthbridge_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE healthbridge_care TO healthbridge_user;
\c healthbridge_care
GRANT ALL ON SCHEMA public TO healthbridge_user;
EOF

# Load schema
psql -U healthbridge_user -d healthbridge_care -f schema/healthbridge_schema.sql
```

### 2. ETL Setup

```bash
# Install Python dependencies
pip install -r etl/requirements.txt

# Configure environment variables
cp etl/.env.example etl/.env
# Edit etl/.env with credentials

# Test ETL scripts
python etl/test_connections.py

# Run full ETL
python etl/run_etl.py
```

### 3. API Deployment

```bash
# Using Docker Compose
cd docker/
docker-compose up -d

# Or manual deployment
cd api/
uvicorn main:app --host 0.0.0.0 --port 8080
```

## API Endpoint

### GET /api/v1/patient/{fiscal_code}

Returns complete patient profile from consolidated database.

**Response Structure:**
```json
{
  "patient": {
    "fiscal_code": "RSSMRA85M01F205X",
    "first_name": "Mario",
    "last_name": "Rossi",
    "birth_date": "1985-01-01",
    ...
  },
  "clinical_events": [...],
  "protected_discharges": [...],
  "data_freshness": {
    "registry_last_update": "2025-02-16T10:30:00Z",
    "aurora_last_update": "2025-02-16T10:25:00Z",
    "bof_last_update": "2025-02-16T10:20:00Z"
  }
}
```

## Security Notes

- All credentials stored in environment variables (never committed)
- Database passwords must be strong (16+ chars)
- API requires authentication token
- TLS/SSL enabled for all connections
- Audit logging enabled for all queries

## Deployment Checklist

- [ ] PostgreSQL installed on AI1/AI2
- [ ] Database schema loaded
- [ ] ETL scripts configured and tested
- [ ] API deployed and accessible
- [ ] VPN routing configured (10.30.229.16/29)
- [ ] AWS application updated to use new API endpoint
- [ ] Monitoring and logging configured
- [ ] Backup strategy implemented

## Maintenance

### ETL Schedule
- **Registry sync**: Every 15 minutes
- **Aurora sync**: Every 30 minutes
- **BOF sync**: Every 1 hour

### Monitoring
- Check ETL status: `SELECT * FROM etl_metadata;`
- Check data freshness: Query `updated_at` timestamps
- Monitor API logs: `/var/log/healthbridge/api.log`

## Troubleshooting

### ETL Connection Issues
```bash
# Test Registry API
curl -k https://clumiddle.aodv.local/AC/pac/rest/paziente/TEST

# Test Aurora DB
python etl/test_aurora.py

# Test BOF API
python etl/test_bof.py
```

### Database Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Check disk space
df -h /var/lib/postgresql
```

## Contact

For issues or questions, contact the development team.
