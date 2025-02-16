#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up PostgreSQL user and database...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Default values
DB_USER="terminusa_user"
DB_PASSWORD="strongpassword"
DB_NAME="terminusa"

# Create PostgreSQL user
echo -e "${YELLOW}Creating PostgreSQL user...${NC}"
su - postgres -c "psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\""

# Create database
echo -e "${YELLOW}Creating database...${NC}"
su - postgres -c "psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\""

# Grant privileges
echo -e "${YELLOW}Granting privileges...${NC}"
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\""

# Update pg_hba.conf to allow password authentication
PG_HBA_PATH=$(su - postgres -c "psql -t -P format=unaligned -c 'SHOW hba_file';")
echo -e "${YELLOW}Updating PostgreSQL authentication configuration...${NC}"

# Add the new configuration if it doesn't exist
if ! grep -q "host    $DB_NAME    $DB_USER    127.0.0.1/32    md5" "$PG_HBA_PATH"; then
    echo "host    $DB_NAME    $DB_USER    127.0.0.1/32    md5" >> "$PG_HBA_PATH"
fi

# Restart PostgreSQL to apply changes
echo -e "${YELLOW}Restarting PostgreSQL...${NC}"
systemctl restart postgresql

# Update .env file
echo -e "${YELLOW}Updating .env file...${NC}"
if [ -f ".env" ]; then
    # Backup existing .env
    cp .env .env.backup
fi

# Create new .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
fi

# Update DATABASE_URL in .env
sed -i "s#DATABASE_URL=.*#DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME#" .env

echo -e "${GREEN}Database setup completed successfully!${NC}"
echo -e "${YELLOW}Database URL: postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME${NC}"
echo -e "${YELLOW}Please ensure this URL matches the DATABASE_URL in your .env file${NC}"
