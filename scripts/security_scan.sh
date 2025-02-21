#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting security scan...${NC}"

# System security checks
check_system_security() {
    echo -e "\n${YELLOW}Checking system security...${NC}"
    
    # Check firewall status
    if systemctl is-active --quiet ufw; then
        echo -e "${GREEN}✓ Firewall is active${NC}"
    else
        echo -e "${RED}✗ Firewall is inactive${NC}"
    fi
    
    # Check SSH configuration
    if grep -q "PermitRootLogin no" /etc/ssh/sshd_config; then
        echo -e "${GREEN}✓ Root login is disabled${NC}"
    else
        echo -e "${RED}✗ Root login is enabled${NC}"
    fi
    
    # Check file permissions
    if [ "$(stat -c %a /etc/ssl/private)" = "700" ]; then
        echo -e "${GREEN}✓ SSL private key permissions are correct${NC}"
    else
        echo -e "${RED}✗ SSL private key permissions are incorrect${NC}"
    fi
}

# Configuration validation
check_configurations() {
    echo -e "\n${YELLOW}Validating configurations...${NC}"
    
    # Check SSL configuration
    if [ -f "/etc/ssl/certs/terminusa.crt" ] && [ -f "/etc/ssl/private/terminusa.key" ]; then
        echo -e "${GREEN}✓ SSL certificates exist${NC}"
    else
        echo -e "${RED}✗ SSL certificates missing${NC}"
    fi
    
    # Check monitoring configuration
    if [ -f "config/monitoring.py" ] && [ -f "config/monitoring_security.py" ]; then
        echo -e "${GREEN}✓ Monitoring configurations exist${NC}"
    else
        echo -e "${RED}✗ Monitoring configurations missing${NC}"
    fi
}

# Network security tests
check_network_security() {
    echo -e "\n${YELLOW}Checking network security...${NC}"
    
    # Check open ports
    echo -e "Open ports:"
    netstat -tuln | grep LISTEN
    
    # Check established connections
    echo -e "\nEstablished connections:"
    netstat -tun | grep ESTABLISHED
}

# Run all checks
check_system_security
check_configurations
check_network_security

echo -e "\n${GREEN}Security scan completed${NC}"
