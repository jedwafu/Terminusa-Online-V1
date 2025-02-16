#!/bin/bash

# Enable error handling and verbose output
set -e
set -x

# Configuration
REPO_URL="https://github.com/jedwafu/Terminusa-Online-V1.git"
INSTALL_DIR="/root/Terminusa"
SERVICE_NAME="terminusa"

echo "Starting deployment..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Load environment variables from .env file if it exists
if [ -f "$INSTALL_DIR/.env" ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source "$INSTALL_DIR/.env"
    set +a
else
    echo "Error: .env file not found!"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip postfix opendkim opendkim-tools mailutils libsasl2-2 libsasl2-modules fail2ban

# Install/update Python dependencies
echo "Installing/updating dependencies..."
pip3 install -r requirements.txt

# Create logs directory
echo "Creating logs directory..."
mkdir -p /var/log/terminusa/
touch /var/log/terminusa/terminusa.log
touch /var/log/terminusa/terminusa.error.log
chmod 644 /var/log/terminusa/terminusa.log
chmod 644 /var/log/terminusa/terminusa.error.log

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOL
[Unit]
Description=Terminusa Online Game Server
After=network.target postgresql.service postfix.service opendkim.service
Wants=postfix.service opendkim.service

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PYTHONPATH=${INSTALL_DIR}"
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/start_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/terminusa/terminusa.log
StandardError=append:/var/log/terminusa/terminusa.error.log
EnvironmentFile=${INSTALL_DIR}/.env

[Install]
WantedBy=multi-user.target
EOL

# Verify service file
echo "Verifying service file..."
systemd-analyze verify /etc/systemd/system/${SERVICE_NAME}.service

# Make scripts executable
echo "Making scripts executable..."
chmod +x ${INSTALL_DIR}/start_server.py
chmod +x ${INSTALL_DIR}/deploy.sh

# Reload systemd and restart services
echo "Reloading systemd..."
systemctl daemon-reload

echo "Stopping existing service if running..."
systemctl stop ${SERVICE_NAME} || true

echo "Starting services..."
systemctl restart postfix opendkim fail2ban
systemctl enable ${SERVICE_NAME}

echo "Starting Terminusa service..."
systemctl start ${SERVICE_NAME}

echo "Checking service status..."
systemctl status ${SERVICE_NAME}

echo "Deployment completed!"
echo "To view logs:"
echo "  Server logs: tail -f /var/log/terminusa/terminusa.log"
echo "  Error logs: tail -f /var/log/terminusa/terminusa.error.log"
echo "  Email logs: tail -f /var/log/mail.log"
echo "  Monitor status: cat ${INSTALL_DIR}/server_status.json"
