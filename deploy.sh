#!/bin/bash

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
    export $(cat "$INSTALL_DIR/.env" | grep -v '^#' | xargs)
else
    echo "Error: .env file not found!"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip postfix opendkim opendkim-tools mailutils libsasl2-2 libsasl2-modules fail2ban

# Configure Postfix if not already configured
if [ ! -f "/etc/postfix/main.cf.original" ]; then
    echo "Configuring Postfix..."
    # Backup original config
    cp /etc/postfix/main.cf /etc/postfix/main.cf.original
    
    # Update configuration
    cat > /etc/postfix/main.cf << EOL
myhostname = ${DOMAIN_NAME}
mydomain = ${DOMAIN_NAME}
myorigin = \$mydomain
inet_interfaces = all
inet_protocols = ipv4
mydestination = \$myhostname, localhost.\$mydomain, localhost, \$mydomain
mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
smtpd_recipient_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination
smtpd_tls_cert_file = ${SSL_CERT_PATH}
smtpd_tls_key_file = ${SSL_KEY_PATH}
smtpd_tls_security_level = may
smtp_tls_security_level = may
EOL
fi

# Configure OpenDKIM if not already configured
if [ ! -d "/etc/opendkim/keys/${DOMAIN_NAME}" ]; then
    echo "Configuring OpenDKIM..."
    mkdir -p /etc/opendkim/keys/${DOMAIN_NAME}
    
    # Generate DKIM keys
    opendkim-genkey -D /etc/opendkim/keys/${DOMAIN_NAME}/ -d ${DOMAIN_NAME} -s default
    
    # Set permissions
    chown -R opendkim:opendkim /etc/opendkim/keys
    
    # Update configuration
    cat > /etc/opendkim.conf << EOL
Domain                  ${DOMAIN_NAME}
KeyFile                 /etc/opendkim/keys/${DOMAIN_NAME}/default.private
Selector                default
EOL
fi

# Configure fail2ban for Postfix
if [ ! -f "/etc/fail2ban/jail.d/postfix.conf" ]; then
    echo "Configuring fail2ban..."
    cat > /etc/fail2ban/jail.d/postfix.conf << EOL
[postfix]
enabled = true
port = smtp,465,submission
filter = postfix
logpath = /var/log/mail.log
maxretry = 5
findtime = 1800
bantime = 86400
EOL
fi

# Check if directory exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Directory does not exist. Cloning repository..."
    git clone $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
else
    echo "Directory exists. Fetching and resetting to match remote..."
    cd $INSTALL_DIR
    git fetch origin
    git reset --hard origin/master
    git clean -fd
fi

# Install/update Python dependencies
echo "Installing/updating dependencies..."
pip3 install -r requirements.txt

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
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/start_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/terminusa.log
StandardError=append:/var/log/terminusa.error.log
EnvironmentFile=${INSTALL_DIR}/.env

[Install]
WantedBy=multi-user.target
EOL

# Make scripts executable
chmod +x start_server.py
chmod +x deploy.sh

# Reload systemd and restart services
echo "Restarting services..."
systemctl daemon-reload
systemctl restart postfix opendkim fail2ban
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

echo "Deployment completed!"
echo "To view logs:"
echo "  Server logs: journalctl -u ${SERVICE_NAME} -f"
echo "  Email logs: tail -f /var/log/mail.log"
echo "  Monitor status: cat ${INSTALL_DIR}/server_status.json"
