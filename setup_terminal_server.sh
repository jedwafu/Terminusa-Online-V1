#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Terminusa Terminal Server...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Create terminusa user if it doesn't exist
if ! id "terminusa" &>/dev/null; then
    echo -e "${YELLOW}Creating terminusa user...${NC}"
    useradd -r -s /bin/false terminusa
fi

# Create required directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p /opt/terminusa
mkdir -p /var/log/terminusa
chown -R terminusa:terminusa /opt/terminusa
chown -R terminusa:terminusa /var/log/terminusa

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if [ ! -d "/opt/terminusa/venv" ]; then
    python3 -m venv /opt/terminusa/venv
fi
source /opt/terminusa/venv/bin/activate
pip install -r requirements.txt
pip install websockets gevent-websocket

# Copy files
echo -e "${YELLOW}Copying files...${NC}"
cp terminal_server.py /opt/terminusa/
cp models.py /opt/terminusa/
cp .env /opt/terminusa/

# Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chown -R terminusa:terminusa /opt/terminusa
chmod 644 /opt/terminusa/terminal_server.py
chmod 644 /opt/terminusa/models.py
chmod 600 /opt/terminusa/.env

# Install systemd service
echo -e "${YELLOW}Installing systemd service...${NC}"
cp terminusa-terminal.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable terminusa-terminal.service

# Configure log rotation
echo -e "${YELLOW}Configuring log rotation...${NC}"
cat > /etc/logrotate.d/terminusa-terminal << EOF
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

# Start the service
echo -e "${YELLOW}Starting terminal server...${NC}"
systemctl start terminusa-terminal.service

# Check service status
if systemctl is-active --quiet terminusa-terminal.service; then
    echo -e "${GREEN}Terminal server is running!${NC}"
    echo -e "You can check the logs with: journalctl -u terminusa-terminal.service"
else
    echo -e "${RED}Failed to start terminal server. Check logs with: journalctl -u terminusa-terminal.service${NC}"
    exit 1
fi

# Configure nginx reverse proxy for WebSocket
echo -e "${YELLOW}Configuring nginx for WebSocket proxy...${NC}"
cat > /etc/nginx/conf.d/terminusa-terminal.conf << EOF
upstream terminusa_terminal {
    server 127.0.0.1:6789;
}

server {
    listen 443 ssl;
    server_name play.terminusa.online;

    ssl_certificate /etc/letsencrypt/live/play.terminusa.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/play.terminusa.online/privkey.pem;

    location / {
        proxy_pass http://terminusa_terminal;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400; # 24 hours
    }
}
EOF

# Test nginx configuration
nginx -t
if [ $? -eq 0 ]; then
    echo -e "${YELLOW}Restarting nginx...${NC}"
    systemctl restart nginx
    echo -e "${GREEN}Nginx configuration updated successfully!${NC}"
else
    echo -e "${RED}Nginx configuration test failed. Please check the configuration.${NC}"
    exit 1
fi

echo -e "${GREEN}Terminal server setup completed successfully!${NC}"
echo -e "WebSocket server is available at: wss://play.terminusa.online"
echo -e "Monitor the service with: systemctl status terminusa-terminal.service"
