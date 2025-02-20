#!/bin/bash

# Function to display system status
show_system_status() {
    clear
    echo -e "${CYAN}=== System Status ===${NC}\n"
    
    # System Resources
    echo -e "${YELLOW}System Resources:${NC}"
    echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
    echo "Memory Usage: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')"
    echo "Disk Usage: $(df -h / | awk 'NR==2{print $5}')"
    echo
    
    # Service Status
    echo -e "${YELLOW}Service Status:${NC}"
    printf "%-15s %-10s %-20s\n" "Service" "Status" "Port"
    echo "----------------------------------------"
    
    # Check PostgreSQL
    if systemctl is-active --quiet postgresql; then
        printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "PostgreSQL" "Running" "5432"
    else
        printf "%-15s ${RED}%-10s${NC} %-20s\n" "PostgreSQL" "Stopped" "-"
    fi
    
    # Check Redis
    if systemctl is-active --quiet redis-server; then
        printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "Redis" "Running" "6379"
    else
        printf "%-15s ${RED}%-10s${NC} %-20s\n" "Redis" "Stopped" "-"
    fi
    
    # Check Nginx
    if systemctl is-active --quiet nginx; then
        printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "Nginx" "Running" "80,443"
    else
        printf "%-15s ${RED}%-10s${NC} %-20s\n" "Nginx" "Stopped" "-"
    fi
    
    # Check Flask app
    if screen -list | grep -q "terminusa-flask"; then
        printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "Flask App" "Running" "5000"
    else
        printf "%-15s ${RED}%-10s${NC} %-20s\n" "Flask App" "Stopped" "-"
    fi
    
    # Check Terminal server
    if screen -list | grep -q "terminusa-terminal"; then
        printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "Terminal" "Running" "6789"
    else
        printf "%-15s ${RED}%-10s${NC} %-20s\n" "Terminal" "Stopped" "-"
    fi
    
    echo
    echo -e "${YELLOW}Screen Sessions:${NC}"
    screen -list | grep -v "There are screens" || echo "No active screens"
    
    # Save status to file
    mkdir -p logs
    cat > logs/service_status.json << EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "system": {
        "cpu_usage": "$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%",
        "memory_usage": "$(free -m | awk 'NR==2{printf "%.2f", $3*100/$2}')%",
        "disk_usage": "$(df -h / | awk 'NR==2{print $5}')"
    },
    "services": {
        "postgresql": "$(systemctl is-active postgresql)",
        "redis": "$(systemctl is-active redis-server)",
        "nginx": "$(systemctl is-active nginx)",
        "flask": "$(screen -list | grep -q "terminusa-flask" && echo "running" || echo "stopped")",
        "terminal": "$(screen -list | grep -q "terminusa-terminal" && echo "running" || echo "stopped")"
    }
}
EOF
}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Show status
show_system_status
