#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

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
    printf "%-20s %-10s %-20s\n" "Service" "Status" "Port"
    echo "----------------------------------------------------"
    
    # System Services
    check_system_service "PostgreSQL" "postgresql" "5432"
    check_system_service "Redis" "redis-server" "6379"
    check_system_service "Nginx" "nginx" "80,443"
    check_system_service "Postfix" "postfix" "25"
    
    # Screen Services
    check_screen_service "Flask App" "terminusa-flask" "5000"
    check_screen_service "Terminal Server" "terminusa-terminal" "6789"
    check_screen_service "Game Server" "terminusa-game" "5001"
    check_screen_service "Email Monitor" "terminusa-email" "-"
    check_screen_service "AI Manager" "terminusa-ai" "-"
    check_screen_service "Combat Manager" "terminusa-combat" "-"
    check_screen_service "Economy Systems" "terminusa-economy" "-"
    check_screen_service "Game Mechanics" "terminusa-mechanics" "-"
    
    echo
    echo -e "${YELLOW}Screen Sessions:${NC}"
    screen -list | grep -v "There are screens" || echo "No active screens"
    
    # Save status to file
    save_status_json
}

# Function to check system service
check_system_service() {
    local name=$1
    local service=$2
    local port=$3
    
    if systemctl is-active --quiet $service; then
        printf "%-20s ${GREEN}%-10s${NC} %-20s\n" "$name" "Running" "$port"
        return 0
    else
        printf "%-20s ${RED}%-10s${NC} %-20s\n" "$name" "Stopped" "-"
        return 1
    fi
}

# Function to check screen service
check_screen_service() {
    local name=$1
    local screen=$2
    local port=$3
    
    if screen -list | grep -q "$screen"; then
        printf "%-20s ${GREEN}%-10s${NC} %-20s\n" "$name" "Running" "$port"
        return 0
    else
        printf "%-20s ${RED}%-10s${NC} %-20s\n" "$name" "Stopped" "-"
        return 1
    fi
}

# Function to save status to JSON
save_status_json() {
    mkdir -p logs
    local status_file="logs/service_status.json"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Start JSON object
    cat > "$status_file" << EOF
{
    "timestamp": "$timestamp",
    "system": {
        "cpu_usage": "$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%",
        "memory_usage": "$(free -m | awk 'NR==2{printf "%.2f", $3*100/$2}')%",
        "disk_usage": "$(df -h / | awk 'NR==2{print $5}')"
    },
    "services": {
        "system_services": {
            "postgresql": "$(systemctl is-active postgresql)",
            "redis": "$(systemctl is-active redis-server)",
            "nginx": "$(systemctl is-active nginx)",
            "postfix": "$(systemctl is-active postfix)"
        },
        "application_services": {
            "flask": "$(screen -list | grep -q "terminusa-flask" && echo "running" || echo "stopped")",
            "terminal": "$(screen -list | grep -q "terminusa-terminal" && echo "running" || echo "stopped")",
            "game": "$(screen -list | grep -q "terminusa-game" && echo "running" || echo "stopped")",
            "email_monitor": "$(screen -list | grep -q "terminusa-email" && echo "running" || echo "stopped")",
            "ai_manager": "$(screen -list | grep -q "terminusa-ai" && echo "running" || echo "stopped")",
            "combat_manager": "$(screen -list | grep -q "terminusa-combat" && echo "running" || echo "stopped")",
            "economy_systems": "$(screen -list | grep -q "terminusa-economy" && echo "running" || echo "stopped")",
            "game_mechanics": "$(screen -list | grep -q "terminusa-mechanics" && echo "running" || echo "stopped")"
        }
    }
}
EOF
}

# Show status
show_system_status
