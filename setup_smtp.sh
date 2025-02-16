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

# Create admin user for mail
echo -e "${YELLOW}Creating mail users...${NC}"
if ! id -u admin > /dev/null 2>&1; then
    useradd -m -s /bin/bash admin
fi
usermod -aG mail admin

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

# Configure OpenDKIM socket directory
DKIM_SOCKET_DIR="/var/spool/postfix/opendkim"
mkdir -p "$DKIM_SOCKET_DIR"
chown opendkim:postfix "$DKIM_SOCKET_DIR"
chmod 750 "$DKIM_SOCKET_DIR"

# Configure OpenDKIM
cat > /etc/opendkim.conf << EOF
# Logging
Syslog          yes
SyslogSuccess   yes
LogWhy          yes

# Daemon settings
Mode            sv
Canonicalization        relaxed/simple
Socket          unix:$DKIM_SOCKET_DIR/opendkim.sock
UMask           002
UserID          opendkim:postfix
PidFile         /run/opendkim/opendkim.pid
InternalHosts   127.0.0.1, localhost, terminusa.online

# Signing
Domain          terminusa.online
KeyFile         /etc/opendkim/keys/terminusa.online/default.private
Selector        default
EOF

# Create OpenDKIM run directory
mkdir -p /run/opendkim
chown opendkim:opendkim /run/opendkim
chmod 755 /run/opendkim

# Set Postfix compatibility level
postconf compatibility_level=3.6

# Configure Postfix
echo -e "${YELLOW}Configuring Postfix...${NC}"
postconf -e "smtpd_milters = unix:opendkim/opendkim.sock"
postconf -e "non_smtpd_milters = unix:opendkim/opendkim.sock"
postconf -e "milter_default_action = accept"
postconf -e "milter_protocol = 2"
postconf -e "myhostname = terminusa.online"
postconf -e "mydomain = terminusa.online"
postconf -e "myorigin = \$mydomain"
postconf -e "home_mailbox = Maildir/"
postconf -e "virtual_alias_maps = hash:/etc/postfix/virtual"
postconf -e "alias_maps = hash:/etc/aliases"
postconf -e "alias_database = hash:/etc/aliases"
postconf -e "local_recipient_maps = unix:passwd.byname \$alias_maps"
postconf -e "mydestination = \$myhostname, localhost.\$mydomain, localhost, \$mydomain"
postconf -e "local_transport = local:\$myhostname"

# Configure aliases
echo -e "${YELLOW}Configuring aliases...${NC}"
cat > /etc/aliases << EOF
postmaster: root
root: admin
admin: admin
EOF
postalias /etc/aliases

# Configure virtual aliases
echo -e "${YELLOW}Configuring virtual aliases...${NC}"
cat > /etc/postfix/virtual << EOF
admin@terminusa.online    admin
postmaster@terminusa.online    admin
root@terminusa.online    admin
EOF
postmap /etc/postfix/virtual

# Create mail directories
echo -e "${YELLOW}Setting up mail directories...${NC}"
mkdir -p /home/admin/Maildir/{new,cur,tmp}
chown -R admin:mail /home/admin/Maildir
chmod -R 700 /home/admin/Maildir

# Add postfix user to opendkim group and vice versa
usermod -aG opendkim postfix
usermod -aG postfix opendkim

# Restart services
echo -e "${YELLOW}Restarting services...${NC}"
systemctl enable opendkim
systemctl start opendkim
sleep 2  # Wait for OpenDKIM to start
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
echo -e "${YELLOW}To test the server, run: test-smtp admin@terminusa.online${NC}"
echo -e "${YELLOW}Check mail.log for any errors: tail -f /var/log/mail.log${NC}"

# Test mail setup
echo -e "${YELLOW}Testing mail setup...${NC}"
echo "Test email" | mail -s "Test Email" admin@terminusa.online

# Show mail log
echo -e "${YELLOW}Checking mail log...${NC}"
tail -n 20 /var/log/mail.log
