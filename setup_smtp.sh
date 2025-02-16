#!/bin/bash

# Stop Postfix
systemctl stop postfix

# Backup original config
cp /etc/postfix/main.cf /etc/postfix/main.cf.backup

# Configure Postfix for direct mail delivery
cat > /etc/postfix/main.cf << EOL
# General Settings
myhostname = terminusa.online
mydomain = terminusa.online
myorigin = \$mydomain
inet_interfaces = all
inet_protocols = ipv4

# Mail Delivery Settings
mydestination = \$myhostname, localhost.\$mydomain, localhost, \$mydomain
local_recipient_maps = unix:passwd.byname \$alias_maps
alias_maps = hash:/etc/aliases
alias_database = hash:/etc/aliases

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

# Create virtual alias file
cat > /etc/postfix/virtual << EOL
@terminusa.online     terminusa
postmaster@terminusa.online    root
admin@terminusa.online        root
noreply@terminusa.online     terminusa
EOL

# Create system user for mail handling
useradd -r -m -s /sbin/nologin terminusa

# Update aliases
newaliases
postmap /etc/postfix/virtual

# Set permissions
chown -R postfix:postfix /var/spool/postfix
chmod -R 700 /var/spool/postfix

# Restart Postfix
systemctl restart postfix

# Show status
systemctl status postfix

# Show mail log
echo "Checking mail log..."
tail -f /var/log/mail.log
