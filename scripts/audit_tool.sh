#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Log paths
AUTH_LOG="/var/log/auth.log"
NGINX_LOG="/var/log/nginx/access.log"
APP_LOG="/var/log/terminusa/app.log"
MONITORING_LOG="/var/log/terminusa/monitoring.log"

echo -e "${YELLOW}Starting security audit...${NC}"

# Authentication audit
audit_authentication() {
    echo -e "\n${YELLOW}Auditing authentication events...${NC}"
    
    # Check failed login attempts
    echo -e "\nFailed login attempts (last 24h):"
    grep "Failed password" $AUTH_LOG | grep "$(date -d '24 hours ago' +'%b %d')"
    
    # Check successful logins
    echo -e "\nSuccessful logins (last 24h):"
    grep "Accepted password" $AUTH_LOG | grep "$(date -d '24 hours ago' +'%b %d')"
}

# Authorization checks
audit_authorization() {
    echo -e "\n${YELLOW}Auditing authorization...${NC}"
    
    # Check sudo usage
    echo -e "\nSudo usage (last 24h):"
    grep "sudo:" $AUTH_LOG | grep "$(date -d '24 hours ago' +'%b %d')"
    
    # Check API access
    echo -e "\nAPI access (last hour):"
    grep "api" $NGINX_LOG | grep "$(date -d '1 hour ago' +'%H:')"
}

# Configuration changes audit
audit_configuration() {
    echo -e "\n${YELLOW}Auditing configuration changes...${NC}"
    
    # Check file modifications
    echo -e "\nRecent configuration changes:"
    find /etc/terminusa -type f -mtime -1 -ls 2>/dev/null
    
    # Check monitoring config changes
    echo -e "\nMonitoring configuration changes:"
    grep "config" $MONITORING_LOG | grep "changed"
}

# Access log analysis
analyze_access_logs() {
    echo -e "\n${YELLOW}Analyzing access logs...${NC}"
    
    # Check high traffic IPs
    echo -e "\nTop 10 IPs by request count:"
    awk '{print $1}' $NGINX_LOG | sort | uniq -c | sort -nr | head -n 10
    
    # Check for suspicious patterns
    echo -e "\nSuspicious requests:"
    grep -i "union\|select\|insert\|delete\|update" $NGINX_LOG
}

# Security event tracking
track_security_events() {
    echo -e "\n${YELLOW}Tracking security events...${NC}"
    
    # Check application security events
    echo -e "\nApplication security events:"
    grep -i "security\|warning\|error" $APP_LOG | tail -n 20
    
    # Check monitoring alerts
    echo -e "\nRecent monitoring alerts:"
    grep "ALERT" $MONITORING_LOG | tail -n 20
}

# Generate summary report
generate_report() {
    echo -e "\n${YELLOW}Generating audit report...${NC}"
    
    REPORT_FILE="audit_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== Terminusa Security Audit Report ==="
        echo "Date: $(date)"
        echo "----------------------------------------"
        
        echo "1. Authentication Summary"
        grep "Failed password" $AUTH_LOG | wc -l | xargs echo "Failed login attempts:"
        grep "Accepted password" $AUTH_LOG | wc -l | xargs echo "Successful logins:"
        
        echo -e "\n2. Authorization Summary"
        grep "sudo:" $AUTH_LOG | wc -l | xargs echo "Sudo commands executed:"
        grep "api" $NGINX_LOG | wc -l | xargs echo "API requests:"
        
        echo -e "\n3. Configuration Changes"
        find /etc/terminusa -type f -mtime -1 -ls 2>/dev/null | wc -l | xargs echo "Files modified in last 24h:"
        
        echo -e "\n4. Access Summary"
        awk '{print $1}' $NGINX_LOG | sort | uniq | wc -l | xargs echo "Unique IPs:"
        grep -i "security\|warning\|error" $APP_LOG | wc -l | xargs echo "Security events:"
        
        echo -e "\n=== End of Report ==="
    } > "$REPORT_FILE"
    
    echo -e "${GREEN}Report generated: $REPORT_FILE${NC}"
}

# Run all audit functions
audit_authentication
audit_authorization
audit_configuration
analyze_access_logs
track_security_events
generate_report

echo -e "\n${GREEN}Security audit completed${NC}"
