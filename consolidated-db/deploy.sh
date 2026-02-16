#!/bin/bash
#
# Healthbridge Care+ Consolidated Database Deployment Script
# Target: AI1 (10.30.229.21) or AI2 (10.30.229.22)
# User: react
#

set -e

echo "=========================================="
echo "Healthbridge Care+ Deployment"
echo "=========================================="
echo ""

# Check if running as react user
if [ "$USER" != "react" ]; then
    echo "Warning: This script should be run as user 'react'"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Install Docker
echo "Step 1: Installing Docker..."
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Step 2: Install Docker Compose
echo ""
echo "Step 2: Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not found. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully"
else
    echo "Docker Compose already installed"
fi

# Verify installations
echo ""
echo "Verifying installations..."
docker --version
docker-compose --version

# Step 3: Navigate to docker directory
echo ""
echo "Step 3: Setting up configuration..."
cd docker

# Step 4: Configure environment
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env

    # Generate secure passwords
    DB_PASSWORD=$(openssl rand -base64 24 | tr -d '\n')
    API_TOKEN=$(openssl rand -hex 32 | tr -d '\n')

    # Update .env file
    sed -i "s/CHANGE_THIS_SECURE_PASSWORD/${DB_PASSWORD}/" .env
    sed -i "s/CHANGE_THIS_API_TOKEN/${API_TOKEN}/" .env

    echo ""
    echo "=========================================="
    echo "GENERATED CREDENTIALS - SAVE THESE!"
    echo "=========================================="
    echo "Database Password: ${DB_PASSWORD}"
    echo "API Token: ${API_TOKEN}"
    echo "=========================================="
    echo ""
    echo "Press Enter to continue..."
    read
else
    echo ".env file already exists. Using existing configuration."
fi

# Step 5: Create log directory
echo ""
echo "Step 4: Creating log directory..."
sudo mkdir -p /var/log/healthbridge
sudo chown -R $USER:$USER /var/log/healthbridge

# Step 6: Start services
echo ""
echo "Step 5: Starting Docker services..."
docker-compose up -d

# Step 7: Wait for services to start
echo ""
echo "Waiting 30 seconds for services to initialize..."
sleep 30

# Step 8: Check service status
echo ""
echo "Step 6: Checking service status..."
docker-compose ps

# Step 9: Test database connection
echo ""
echo "Step 7: Testing database connection..."
if docker exec healthbridge_postgres pg_isready -U healthbridge_user > /dev/null 2>&1; then
    echo "Database connection: OK"
else
    echo "Database connection: FAILED"
    exit 1
fi

# Step 10: Test data source connections
echo ""
echo "Step 8: Testing data source connections..."
echo "This will test Registry API, Aurora DB, and BOF API..."
docker exec healthbridge_etl python test_connections.py

# Step 11: Test API endpoint
echo ""
echo "Step 9: Testing API endpoint..."
API_STATUS=$(curl -s http://localhost:8080/status)
if echo "$API_STATUS" | grep -q "healthy"; then
    echo "API health check: OK"
else
    echo "API health check: FAILED"
    echo "Response: $API_STATUS"
fi

# Step 12: Get API token from .env
API_TOKEN=$(grep "^API_TOKEN=" .env | cut -d'=' -f2)

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Services running:"
docker-compose ps
echo ""
echo "API Endpoint: http://$(hostname -I | awk '{print $1}'):8080"
echo "API Token: ${API_TOKEN}"
echo ""
echo "Next steps:"
echo ""
echo "1. Update AWS backend .env file with:"
echo "   CONSOLIDATED_API_URL=http://$(hostname -I | awk '{print $1}'):8080"
echo "   CONSOLIDATED_API_TOKEN=${API_TOKEN}"
echo ""
echo "2. Test patient endpoint:"
echo "   curl -H 'Authorization: Bearer ${API_TOKEN}' \\"
echo "        http://localhost:8080/api/v1/patient/RSSMRA85M01F205X"
echo ""
echo "3. Monitor logs:"
echo "   docker-compose logs -f"
echo ""
echo "4. Check ETL status:"
echo "   docker exec healthbridge_postgres psql -U healthbridge_user -d healthbridge_care -c 'SELECT * FROM etl_metadata;'"
echo ""
echo "=========================================="
