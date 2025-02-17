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

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}Installing PostgreSQL...${NC}"
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
fi

# Create database user if it doesn't exist
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo -e "${YELLOW}Creating database user...${NC}"
    sudo -u postgres createuser $DB_USER
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH SUPERUSER;"
fi

# Create database if it doesn't exist
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo -e "${YELLOW}Creating database...${NC}"
    sudo -u postgres createdb $DB_NAME -O $DB_USER
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
fi

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-updated.txt

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
export PYTHONPATH=$PWD
export FLASK_APP=app.py
flask db upgrade

# Create static directories if they don't exist
echo -e "${YELLOW}Setting up static files...${NC}"
mkdir -p static/css static/js static/images
chmod -R 755 static

# Set up Nginx
echo -e "${YELLOW}Setting up Nginx...${NC}"
if [ ! -f "/etc/nginx/sites-available/terminusa" ]; then
    sudo cp nginx/terminusa.conf /etc/nginx/sites-available/
    sudo ln -s /etc/nginx/sites-available/terminusa /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
fi

# Verify and restart Nginx
echo -e "${YELLOW}Verifying Nginx configuration...${NC}"
sudo nginx -t
if [ $? -eq 0 ]; then
    echo -e "${YELLOW}Restarting Nginx...${NC}"
    sudo systemctl restart nginx
else
    echo -e "${RED}Nginx configuration test failed${NC}"
    exit 1
fi

# Set proper permissions
echo -e "${YELLOW}Setting file permissions...${NC}"
sudo chown -R www-data:www-data static
sudo chmod -R 755 static

# Start services
echo -e "${YELLOW}Starting services...${NC}"
sudo bash start_server.sh restart

echo -e "${GREEN}Deployment complete!${NC}"
