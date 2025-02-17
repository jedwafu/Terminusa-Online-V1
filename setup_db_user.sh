#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    source .env
    # Extract database credentials from DATABASE_URL
    if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^/]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASSWORD="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_NAME="${BASH_REMATCH[4]}"
    else
        echo -e "${RED}Invalid DATABASE_URL format in .env file${NC}"
        exit 1
    fi
else
    echo -e "${RED}.env file not found${NC}"
    exit 1
fi

# Create database user
echo -e "${YELLOW}Creating database user...${NC}"
sudo -u postgres createuser $DB_USER 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "ALTER USER $DB_USER WITH SUPERUSER;"

# Create database
echo -e "${YELLOW}Creating database...${NC}"
sudo -u postgres createdb $DB_NAME -O $DB_USER 2>/dev/null || true

echo -e "${YELLOW}Database URL: $DATABASE_URL${NC}"

# Test connection
echo -e "${YELLOW}Testing database connection...${NC}"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt" >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database setup completed successfully!${NC}"
else
    echo -e "${RED}Failed to connect to database. Please check your configuration.${NC}"
    exit 1
fi
