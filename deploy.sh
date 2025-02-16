#!/bin/bash

# Enable error handling and verbose output
set -e
set -x

# Configuration
REPO_URL="https://github.com/jedwafu/Terminusa-Online-V1.git"
INSTALL_DIR="/root/Terminusa"
SERVICE_NAME="terminusa"
DOMAIN_NAME="terminusa.online"

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
apt-get install -y python3 python3-pip postfix opendkim opendkim-tools mailutils \
    libsasl2-2 libsasl2-modules fail2ban net-tools ufw curl wget

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

# Configure firewall
echo "Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 25/tcp    # SMTP
ufw allow 465/tcp   # SMTPS
ufw allow 587/tcp   # Submission
ufw allow 5000/tcp  # Game Server
ufw allow 5001/tcp  # Web Server

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

# Display DKIM key for DNS configuration
echo "DKIM key for DNS configuration:"
cat /etc/opendkim/keys/${DOMAIN_NAME}/default.txt

echo "Deployment completed!"
echo "To view logs:"
echo "  Server logs: tail -f /var/log/terminusa/terminusa.log"
echo "  Error logs: tail -f /var/log/terminusa/terminusa.error.log"
echo "  Email logs: tail -f /var/log/mail.log"
echo "  Monitor status: cat ${INSTALL_DIR}/server_status.json"

echo "Don't forget to add these DNS records:"
echo "1. MX record: @ IN MX 10 ${DOMAIN_NAME}."
echo "2. SPF record: @ IN TXT \"v=spf1 ip4:$(curl -s ifconfig.me) ~all\""
echo "3. DKIM record (shown above)"
echo "4. DMARC record: _dmarc IN TXT \"v=DMARC1;p=none;rua=mailto:admin@${DOMAIN_NAME}\""
