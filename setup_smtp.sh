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
    DEBIAN_FRONTEND=noninteractive apt-get install -y postfix opendkim opendkim-tools mailutils
elif [ -f /etc/redhat-release ]; then
    # RHEL/CentOS
    yum install -y postfix opendkim mailx
else
    echo -e "${RED}Unsupported distribution. Please install Postfix manually.${NC}"
    exit 1
fi

# Stop services for configuration
systemctl stop postfix opendkim

# Backup original configurations
echo -e "${YELLOW}Backing up original configurations...${NC}"
cp /etc/postfix/main.cf /etc/postfix/main.cf.backup
cp /etc/opendkim.conf /etc/opendkim.conf.backup

# Configure OpenDKIM
echo -e "${YELLOW}Configuring OpenDKIM...${NC}"
mkdir -p /etc/opendkim/keys/terminusa.online
chown -R opendkim:opendkim /etc/opendkim
chmod -R 750 /etc/opendkim

# Generate DKIM keys
opendkim-genkey -D /etc/opendkim/keys/terminusa.online/ -d terminusa.online -s default
chown opendkim:opendkim /etc/opendkim/keys/terminusa.online/default.private
chmod 600 /etc/opendkim/keys/terminusa.online/default.private

# Configure OpenDKIM
cat > /etc/opendkim.conf << EOF
Syslog          yes
UMask           002
Domain          terminusa.online
KeyFile         /etc/opendkim/keys/terminusa.online/default.private
Selector        default
Socket          inet:8891@localhost
EOF

# Set Postfix compatibility level
postconf compatibility_level=3.6

# Configure Postfix
echo -e "${YELLOW}Configuring Postfix...${NC}"
cat > /etc/postfix/main.cf << EOF
# Basic Configuration
compatibility_level = 3.6
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

# DKIM Configuration
milter_default_action = accept
milter_protocol = 2
smtpd_milters = inet:localhost:8891
non_smtpd_milters = inet:localhost:8891

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

# Chroot configuration
queue_directory = /var/spool/postfix
command_directory = /usr/sbin
daemon_directory = /usr/lib/postfix/sbin
data_directory = /var/lib/postfix
mail_owner = postfix
setgid_group = postdrop
EOF

# Create and set permissions for mail directories
echo -e "${YELLOW}Setting up mail directories...${NC}"
mkdir -p /var/mail
mkdir -p /var/spool/postfix/pid
mkdir -p /var/spool/postfix/public
mkdir -p /var/spool/postfix/private
mkdir -p /var/spool/postfix/etc
mkdir -p /var/spool/postfix/lib
mkdir -p /var/spool/postfix/usr

# Set correct ownership and permissions
chown -R root:root /var/spool/postfix
chown -R postfix:root /var/spool/postfix/pid
chown -R postfix:postdrop /var/spool/postfix/public
chown -R postfix:postfix /var/spool/postfix/private
chmod 755 /var/mail
chmod 755 /var/spool/postfix
chmod 700 /var/spool/postfix/pid
chmod 710 /var/spool/postfix/public
chmod 700 /var/spool/postfix/private

# Copy necessary files to chroot
cp /etc/services /var/spool/postfix/etc/
cp /etc/resolv.conf /var/spool/postfix/etc/
cp -r /etc/ssl /var/spool/postfix/etc/
cp /etc/localtime /var/spool/postfix/etc/
cp /etc/nsswitch.conf /var/spool/postfix/etc/
cp /etc/hosts /var/spool/postfix/etc/
cp /etc/passwd /var/spool/postfix/etc/

# Set correct ownership for chroot files
chown -R root:root /var/spool/postfix/etc
chown -R root:root /var/spool/postfix/lib
chown -R root:root /var/spool/postfix/usr

# Run Postfix's built-in permission fixer
echo -e "${YELLOW}Running Postfix permission fixes...${NC}"
postfix set-permissions
postfix check

# Restart services
echo -e "${YELLOW}Restarting services...${NC}"
systemctl enable opendkim
systemctl start opendkim
systemctl enable postfix
systemctl start postfix

# Test configuration
echo -e "${YELLOW}Testing Postfix configuration...${NC}"
if postfix check; then
    echo -e "${GREEN}Postfix configuration test passed${NC}"
else
    echo -e "${RED}Postfix configuration test failed${NC}"
    exit 1
fi

# Display DKIM record
echo -e "${YELLOW}Add this TXT record to your DNS:${NC}"
cat /etc/opendkim/keys/terminusa.online/default.txt

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

# Test mail setup
echo -e "${YELLOW}Testing mail setup...${NC}"
echo "Test email" | mail -s "Test Email" admin@terminusa.online

# Show mail log
echo -e "${YELLOW}Checking mail log...${NC}"
tail -n 20 /var/log/mail.log
