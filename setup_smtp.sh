#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Postfix SMTP Server...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Install Postfix and related packages
echo -e "${YELLOW}Installing Postfix and dependencies...${NC}"
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y postfix mailutils
elif [ -f /etc/redhat-release ]; then
    # RHEL/CentOS
    yum install -y postfix mailx
else
    echo -e "${RED}Unsupported distribution. Please install Postfix manually.${NC}"
    exit 1
fi

# Backup original Postfix configuration
echo -e "${YELLOW}Backing up original configuration...${NC}"
cp /etc/postfix/main.cf /etc/postfix/main.cf.backup

# Configure Postfix
echo -e "${YELLOW}Configuring Postfix...${NC}"
cat > /etc/postfix/main.cf << EOF
# Basic Configuration
smtpd_banner = \$myhostname ESMTP Terminusa Mail Server
biff = no
append_dot_mydomain = no
readme_directory = no

# TLS Configuration
smtpd_tls_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
smtpd_tls_key_file=/etc/ssl/private/ssl-cert-snakeoil.key
smtpd_use_tls=yes
smtpd_tls_auth_only = yes
smtp_tls_security_level = may
smtpd_tls_security_level = may

# Network Configuration
myhostname = terminusa.online
mydomain = terminusa.online
myorigin = \$mydomain
inet_interfaces = all
inet_protocols = ipv4
mydestination = \$myhostname, localhost.\$mydomain, localhost, \$mydomain
mynetworks = 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
relayhost =

# Mail Directory
home_mailbox = Maildir/
mail_spool_directory = /var/mail

# Security
smtpd_helo_required = yes
disable_vrfy_command = yes
smtpd_delay_reject = yes

# Access Control
smtpd_recipient_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination

# Size Limits
message_size_limit = 10485760
mailbox_size_limit = 1073741824

# Performance
maximal_queue_lifetime = 1h
bounce_queue_lifetime = 1h
EOF

# Create required directories
echo -e "${YELLOW}Creating mail directories...${NC}"
mkdir -p /var/spool/postfix
mkdir -p /var/mail
chmod 755 /var/mail

# Restart Postfix
echo -e "${YELLOW}Restarting Postfix...${NC}"
systemctl enable postfix
systemctl restart postfix

# Test configuration
echo -e "${YELLOW}Testing Postfix configuration...${NC}"
if postfix check; then
    echo -e "${GREEN}Postfix configuration test passed${NC}"
else
    echo -e "${RED}Postfix configuration test failed${NC}"
    exit 1
fi

# Open firewall ports
echo -e "${YELLOW}Configuring firewall...${NC}"
if command -v ufw > /dev/null; then
    # Ubuntu/Debian with UFW
    ufw allow 25/tcp
    ufw allow 587/tcp
elif command -v firewall-cmd > /dev/null; then
    # RHEL/CentOS with firewalld
    firewall-cmd --permanent --add-service=smtp
    firewall-cmd --permanent --add-port=587/tcp
    firewall-cmd --reload
fi

# Create test script
echo -e "${YELLOW}Creating test script...${NC}"
cat > /usr/local/bin/test-smtp << EOF
#!/bin/bash
echo "This is a test email from Terminusa SMTP Server" | mail -s "Test Email" \$1
EOF
chmod +x /usr/local/bin/test-smtp

echo -e "${GREEN}SMTP Server setup complete!${NC}"
echo -e "${YELLOW}To test the server, run: test-smtp your@email.com${NC}"
echo -e "${YELLOW}Check mail.log for any errors: tail -f /var/log/mail.log${NC}"
