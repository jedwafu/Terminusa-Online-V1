#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check command status
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}Starting Terminusa Online deployment...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Install system dependencies
echo -e "\n${YELLOW}Installing system dependencies...${NC}"
apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    redis-server \
    supervisor \
    certbot \
    python3-certbot-nginx
check_status

# Create application directory
echo -e "\n${YELLOW}Creating application directory...${NC}"
mkdir -p /opt/terminusa
mkdir -p /var/log/terminusa
check_status

# Create terminusa user
echo -e "\n${YELLOW}Creating terminusa user...${NC}"
useradd -r -s /bin/false terminusa || true
check_status

# Set up Python virtual environment
echo -e "\n${YELLOW}Setting up Python virtual environment...${NC}"
python3 -m venv /opt/terminusa/venv
source /opt/terminusa/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
check_status

# Copy application files
echo -e "\n${YELLOW}Copying application files...${NC}"
cp -r * /opt/terminusa/
check_status

# Set up environment variables
echo -e "\n${YELLOW}Setting up environment variables...${NC}"
if [ ! -f "/opt/terminusa/.env" ]; then
    cp .env.example /opt/terminusa/.env
    echo -e "${YELLOW}Please update /opt/terminusa/.env with your configuration${NC}"
fi

# Set up database
echo -e "\n${YELLOW}Setting up database...${NC}"
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw terminusa_db; then
    sudo -u postgres createuser terminusa
    sudo -u postgres createdb terminusa_db
    DB_PASSWORD=$(openssl rand -hex 16)
    sudo -u postgres psql -c "ALTER USER terminusa WITH PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE terminusa_db TO terminusa;"
    
    # Update DATABASE_URL in .env
    sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql://terminusa:$DB_PASSWORD@localhost:5432/terminusa_db|g" /opt/terminusa/.env
fi
check_status

# Initialize database and run migrations
echo -e "\n${YELLOW}Initializing database and running migrations...${NC}"
cd /opt/terminusa
source venv/bin/activate
export FLASK_APP=app.py
export FLASK_ENV=development

# Run database migrations
flask db upgrade head
check_status

# Initialize database with admin user
python init_database.py
check_status

# Set up SSL certificates
echo -e "\n${YELLOW}Setting up SSL certificates...${NC}"
if [ ! -d "/etc/letsencrypt/live/terminusa.online" ]; then
    certbot --nginx -d terminusa.online -d play.terminusa.online --non-interactive --agree-tos --email admin@terminusa.online
fi
check_status

# Configure nginx
echo -e "\n${YELLOW}Configuring nginx...${NC}"
cp nginx/terminusa.conf /etc/nginx/conf.d/
cp nginx/terminusa-terminal.conf /etc/nginx/conf.d/
nginx -t
check_status

# Set up systemd services
echo -e "\n${YELLOW}Setting up systemd services...${NC}"
cp terminusa-terminal.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable terminusa-terminal.service
systemctl enable nginx
check_status

# Configure log rotation
echo -e "\n${YELLOW}Configuring log rotation...${NC}"
cat > /etc/logrotate.d/terminusa << EOF
/var/log/terminusa/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 640 terminusa terminusa
}
EOF
check_status

# Set permissions
echo -e "\n${YELLOW}Setting permissions...${NC}"
chown -R terminusa:terminusa /opt/terminusa
chown -R terminusa:terminusa /var/log/terminusa
chmod -R 755 /opt/terminusa
chmod 600 /opt/terminusa/.env
check_status

# Start services
echo -e "\n${YELLOW}Starting services...${NC}"
systemctl restart nginx

# Start terminal server
echo -e "\n${YELLOW}Starting terminal server...${NC}"
systemctl start terminusa-terminal.service
check_status

# Start web application
echo -e "\n${YELLOW}Starting web application...${NC}"
cd /opt/terminusa
source venv/bin/activate
python app_final.py &
check_status

# Verify deployment
echo -e "\n${YELLOW}Verifying deployment...${NC}"
if systemctl is-active --quiet nginx && systemctl is-active --quiet terminusa-terminal.service; then
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "\nServices status:"
    echo -e "Nginx: $(systemctl is-active nginx)"
    echo -e "Terminal Server: $(systemctl is-active terminusa-terminal.service)"
    echo -e "Web Application: Running"
    
    echo -e "\nAccess points:"
    echo -e "Main website: https://terminusa.online"
    echo -e "Game terminal: https://play.terminusa.online"
    
    echo -e "\nLog files:"
    echo -e "Main logs: /var/log/terminusa/app.log"
    echo -e "Terminal logs: /var/log/terminusa/terminal.log"
    
    echo -e "\nMonitor services with:"
    echo -e "journalctl -u terminusa-terminal.service -f"
    echo -e "tail -f /var/log/terminusa/*.log"
    
    echo -e "\nDefault admin credentials:"
    echo -e "Username: adminbb"
    echo -e "Email: admin@terminusa.online"
    echo -e "\n${YELLOW}Please change admin password after first login!${NC}"
else
    echo -e "${RED}Deployment verification failed. Please check the logs.${NC}"
    exit 1
fi
