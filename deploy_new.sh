#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p logs
mkdir -p instance
mkdir -p static/downloads

# Set proper permissions
chmod -R 755 static
chmod +x *.py

# Set up Nginx
echo -e "${YELLOW}Setting up Nginx...${NC}"
# Always update nginx config
sudo cp nginx/terminusa.conf /etc/nginx/sites-available/terminusa
sudo ln -sf /etc/nginx/sites-available/terminusa /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo -e "${YELLOW}Testing Nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}Nginx configuration test successful${NC}"
    sudo systemctl restart nginx
else
    echo -e "${RED}Nginx configuration test failed${NC}"
    exit 1
fi

# Run database migrations and setup
echo -e "${YELLOW}Running database migrations and setup...${NC}"
export PYTHONPATH=$PWD
export FLASK_APP=app_merged.py

# Run migrations
flask db upgrade

# Create initial announcement
echo -e "${YELLOW}Creating initial announcement...${NC}"
python3 create_initial_announcement.py

# Set up static files and permissions
echo -e "${YELLOW}Setting up static files...${NC}"
mkdir -p static/css static/js static/images
sudo chown -R www-data:www-data static
sudo chmod -R 755 static

# Restart services
echo -e "${YELLOW}Restarting services...${NC}"
sudo systemctl restart nginx
sudo systemctl restart postgresql
sudo systemctl restart postfix

# Start application server
echo -e "${YELLOW}Starting application server...${NC}"
bash start_server.sh restart

echo -e "${GREEN}Deployment complete!${NC}"
