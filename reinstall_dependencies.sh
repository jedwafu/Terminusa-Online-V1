#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check command status
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Success${NC}"
    else
        echo -e "${RED}Failed${NC}"
        exit 1
    fi
}

echo -e "${GREEN}Reinstalling Terminusa Online Dependencies${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
echo -e "${YELLOW}Creating logs directory...${NC}"
mkdir -p logs
chmod 777 logs
check_status

# Stop services
echo -e "${YELLOW}Stopping services...${NC}"
systemctl stop gunicorn
systemctl stop nginx
check_status

# Remove existing virtual environment
echo -e "${YELLOW}Removing existing virtual environment...${NC}"
if [ -d "venv" ]; then
    rm -rf venv
fi
check_status

# Create new virtual environment
echo -e "${YELLOW}Creating new virtual environment...${NC}"
python3 -m venv venv
check_status

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
check_status

# Upgrade pip and basic tools
echo -e "${YELLOW}Upgrading pip and basic tools...${NC}"
pip install --upgrade pip setuptools wheel
check_status

# Remove problematic packages
echo -e "${YELLOW}Removing problematic packages...${NC}"
pip uninstall -y pyOpenSSL cryptography typing-extensions
check_status

# Install base dependencies
echo -e "${YELLOW}Installing base dependencies...${NC}"
pip install -r requirements-base.txt
check_status

# Install optional dependencies
echo -e "${YELLOW}Installing optional dependencies...${NC}"
pip install -r requirements-optional.txt || {
    echo -e "${YELLOW}Some optional dependencies failed to install. Continuing...${NC}"
}

# Verify critical installations
echo -e "${YELLOW}Verifying critical installations...${NC}"
python3 -c "
import flask
import sqlalchemy
import bcrypt
import cryptography
import OpenSSL
print('Critical dependencies verified successfully!')
"
check_status

# Set proper permissions
echo -e "${YELLOW}Setting proper permissions...${NC}"
chown -R www-data:www-data .
chmod -R 755 .
chmod -R 777 logs
chmod +x *.sh
check_status

# Update Gunicorn service
echo -e "${YELLOW}Updating Gunicorn service...${NC}"
cat > /etc/systemd/system/gunicorn.service << EOL
[Unit]
Description=Gunicorn instance to serve Terminusa
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/root/Terminusa
Environment="PATH=/root/Terminusa/venv/bin"
ExecStart=/root/Terminusa/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app_final:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL
check_status

# Reload systemd
echo -e "${YELLOW}Reloading systemd...${NC}"
systemctl daemon-reload
check_status

# Start services
echo -e "${YELLOW}Starting services...${NC}"
systemctl start gunicorn
systemctl start nginx
check_status

# Enable services
echo -e "${YELLOW}Enabling services...${NC}"
systemctl enable gunicorn
systemctl enable nginx
check_status

echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${YELLOW}Services status:${NC}"
echo -e "Gunicorn: $(systemctl is-active gunicorn)"
echo -e "Nginx: $(systemctl is-active nginx)"

echo -e "\n${YELLOW}If you encounter any issues, check the logs:${NC}"
echo -e "1. Gunicorn logs: ${GREEN}journalctl -u gunicorn${NC}"
echo -e "2. Nginx logs: ${GREEN}tail -f /var/log/nginx/error.log${NC}"
echo -e "3. Application logs: ${GREEN}tail -f logs/*.log${NC}"

echo -e "\n${GREEN}Setup complete! The server should now be running.${NC}"
