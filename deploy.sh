#!/bin/bash

# Enable error handling and verbose output
set -e
set -x

# Configuration
REPO_URL="https://github.com/jedwafu/terminusa-online"
INSTALL_DIR="/root/Terminusa"
SERVICE_NAME="terminusa"
DOMAIN_NAME="terminusa.online"

echo "Starting deployment..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Create required directories
mkdir -p ${INSTALL_DIR}/logs
mkdir -p ${INSTALL_DIR}/static/css
mkdir -p ${INSTALL_DIR}/static/js
mkdir -p ${INSTALL_DIR}/static/images
mkdir -p ${INSTALL_DIR}/templates

# Set proper permissions
chown -R root:root ${INSTALL_DIR}
chmod -R 755 ${INSTALL_DIR}
chmod -R 777 ${INSTALL_DIR}/logs

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip postfix opendkim opendkim-tools mailutils \
    libsasl2-2 libsasl2-modules fail2ban net-tools ufw curl wget nginx

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r ${INSTALL_DIR}/requirements.txt

# Configure Nginx
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/terminusa << EOL
server {
    listen 80;
    server_name terminusa.online www.terminusa.online;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /static {
        alias ${INSTALL_DIR}/static;
    }

    location /templates {
        alias ${INSTALL_DIR}/templates;
    }
}
EOL

# Enable the site
ln -sf /etc/nginx/sites-available/terminusa /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Configure systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOL
[Unit]
Description=Terminusa Online Game Server
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PYTHONPATH=${INSTALL_DIR}"
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/terminusa/terminusa.log
StandardError=append:/var/log/terminusa/terminusa.error.log

[Install]
WantedBy=multi-user.target
EOL

# Configure firewall
echo "Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 5000/tcp  # Flask
ufw allow 5001/tcp  # Web Server

# Reload services
echo "Reloading services..."
systemctl daemon-reload
systemctl restart nginx
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

# Display status
echo "Checking service status..."
systemctl status ${SERVICE_NAME}
systemctl status nginx

echo "Deployment completed!"
echo "To view logs:"
echo "  Server logs: tail -f /var/log/terminusa/terminusa.log"
echo "  Error logs: tail -f /var/log/terminusa/terminusa.error.log"
echo "  Nginx logs: tail -f /var/log/nginx/access.log"
