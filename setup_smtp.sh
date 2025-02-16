#!/bin/bash

# Stop services
systemctl stop postfix opendkim

# Backup original configs
cp /etc/postfix/main.cf /etc/postfix/main.cf.backup
cp /etc/opendkim.conf /etc/opendkim.conf.backup

# Create mail directories
mkdir -p /var/mail/vhosts/terminusa.online
mkdir -p /var/mail/vhosts/admin
mkdir -p /var/mail/vhosts/noreply

# Create virtual users and domains
cat > /etc/postfix/virtual_domains << EOL
terminusa.online OK
EOL

cat > /etc/postfix/virtual_mailbox_maps << EOL
admin@terminusa.online    terminusa.online/admin/
noreply@terminusa.online  terminusa.online/noreply/
EOL

cat > /etc/postfix/virtual_alias_maps << EOL
postmaster@terminusa.online    admin@terminusa.online
abuse@terminusa.online         admin@terminusa.online
EOL

# Create mail user and group
groupadd -g 5000 vmail
useradd -g vmail -u 5000 vmail -d /var/mail/vhosts -m -s /sbin/nologin

# Set permissions
chown -R vmail:vmail /var/mail/vhosts
chmod -R 770 /var/mail/vhosts

# Configure Postfix
cat > /etc/postfix/main.cf << EOL
# General Settings
myhostname = terminusa.online
mydomain = terminusa.online
myorigin = \$mydomain
inet_interfaces = all
inet_protocols = ipv4

# Virtual Domain Settings
virtual_mailbox_domains = /etc/postfix/virtual_domains
virtual_mailbox_base = /var/mail/vhosts
virtual_mailbox_maps = hash:/etc/postfix/virtual_mailbox_maps
virtual_alias_maps = hash:/etc/postfix/virtual_alias_maps
virtual_minimum_uid = 5000
virtual_uid_maps = static:5000
virtual_gid_maps = static:5000
virtual_transport = virtual

# Network Settings
mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
smtpd_recipient_restrictions = 
    permit_mynetworks,
    reject_unauth_destination,
    reject_invalid_hostname,
    reject_non_fqdn_hostname,
    reject_non_fqdn_sender,
    reject_non_fqdn_recipient,
    reject_unknown_sender_domain,
    reject_unknown_recipient_domain,
    reject_rbl_client zen.spamhaus.org

# TLS Settings
smtpd_tls_cert_file = /etc/letsencrypt/live/terminusa.online/fullchain.pem
smtpd_tls_key_file = /etc/letsencrypt/live/terminusa.online/privkey.pem
smtpd_tls_security_level = may
smtp_tls_security_level = may
smtpd_tls_protocols = !SSLv2, !SSLv3
smtp_tls_protocols = !SSLv2, !SSLv3

# Performance Settings
maximal_queue_lifetime = 1h
bounce_queue_lifetime = 1h
maximal_backoff_time = 15m
minimal_backoff_time = 5m
queue_run_delay = 5m

# Logging Settings
debug_peer_level = 2
maillog_file = /var/log/mail.log
EOL

# Hash the maps
postmap /etc/postfix/virtual_mailbox_maps
postmap /etc/postfix/virtual_alias_maps

# Fix permissions for chroot
for dir in /var/spool/postfix/usr/lib /var/spool/postfix/usr/lib/sasl2 /var/spool/postfix/usr/lib/zoneinfo; do
    if [ -d "$dir" ]; then
        chown root:root "$dir"
    fi
done

# Configure OpenDKIM
cat > /etc/opendkim.conf << EOL
Domain                  terminusa.online
KeyFile                 /etc/opendkim/keys/terminusa.online/default.private
Selector                default
Socket                  inet:8891@localhost
PidFile                /var/run/opendkim/opendkim.pid
SignatureAlgorithm     rsa-sha256
UserID                 opendkim:opendkim
UMask                  022
OversignHeaders        From
TrustAnchorFile        /usr/share/dns/root.key
EOL

# Generate DKIM keys if not exists
if [ ! -d "/etc/opendkim/keys/terminusa.online" ]; then
    mkdir -p /etc/opendkim/keys/terminusa.online
    opendkim-genkey -D /etc/opendkim/keys/terminusa.online/ -d terminusa.online -s default
    chown -R opendkim:opendkim /etc/opendkim/keys
fi

# Start services
systemctl start opendkim
systemctl start postfix

# Show status
systemctl status postfix
systemctl status opendkim

# Show DKIM key for DNS
echo "Add this TXT record to your DNS:"
echo ""
cat /etc/opendkim/keys/terminusa.online/default.txt
echo ""
echo "Testing mail setup..."
echo "Test email" | mail -s "SMTP Test" admin@terminusa.online

# Show mail log
echo "Checking mail log..."
tail -f /var/log/mail.log
