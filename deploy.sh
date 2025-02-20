#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Debug mode flag
DEBUG=false

# Service status tracking
declare -A SERVICE_STATUS
declare -A SERVICE_PIDS
declare -A SERVICE_PORTS
declare -A SERVICE_LOGS
declare -A SERVICE_SCREENS

# Initialize service configurations
SERVICE_PORTS=(
    ["postgresql"]="5432"
    ["nginx"]="80,443"
    ["flask"]="5000"
    ["terminal"]="6789"
    ["redis"]="6379"
)

SERVICE_LOGS=(
    ["postgresql"]="/var/log/postgresql/postgresql-main.log"
    ["nginx"]="/var/log/nginx/error.log"
    ["flask"]="logs/flask.log"
    ["terminal"]="logs/terminal.log"
    ["redis"]="/var/log/redis/redis-server.log"
)

SERVICE_SCREENS=(
    ["flask"]="terminusa-flask"
    ["terminal"]="terminusa-terminal"
)

# Monitoring variables
MONITOR_INTERVAL=5  # seconds
MONITOR_RUNNING=true

# Debug logging function
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

# Error logging function
error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Success logging function
success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Info logging function
info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Check Python version
check_python() {
    info_log "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        error_log "Python 3 is not installed!"
        return 1
    fi
    
    python3_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$python3_version < 3.10" | bc -l) )); then
        error_log "Python 3.10 or later is required!"
        return 1
    fi
    
    success_log "Python $python3_version found"
    return 0
}

# Check PostgreSQL installation
check_postgresql() {
    info_log "Checking PostgreSQL installation..."
    if ! command -v psql &> /dev/null; then
        error_log "PostgreSQL is not installed!"
        echo -e "${YELLOW}Please install PostgreSQL:${NC}"
        echo "1. sudo apt update"
        echo "2. sudo apt install postgresql postgresql-contrib"
        echo "3. sudo systemctl enable postgresql"
        echo "4. sudo systemctl start postgresql"
        return 1
    fi
    
    if ! systemctl is-active --quiet postgresql; then
        error_log "PostgreSQL is not running!"
        return 1
    fi
    
    success_log "PostgreSQL is installed and running"
    return 0
}

# Check if screen is installed
check_screen() {
    if ! command -v screen &> /dev/null; then
        info_log "Installing screen..."
        apt-get update && apt-get install -y screen
    fi
}

# Start a screen session
start_screen() {
    local name=$1
    local command=$2
    screen -dmS $name bash -c "$command"
}

# Check if a screen session exists
check_screen_session() {
    local name=$1
    screen -list | grep -q "$name"
}

# Kill a screen session
kill_screen() {
    local name=$1
    screen -X -S $name quit >/dev/null 2>&1
}

# Save service status to JSON
save_status() {
    local status_file="logs/service_status.json"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}')
    local mem_usage=$(free -m | awk 'NR==2{printf "%.2f", $3*100/$2}')
    local disk_usage=$(df -h / | awk 'NR==2{print $5}')
    
    cat > "$status_file" << EOF
{
    "timestamp": "$timestamp",
    "system": {
        "cpu_usage": "$cpu_usage%",
        "memory_usage": "$mem_usage%",
        "disk_usage": "$disk_usage"
    },
    "services": {
EOF
    
    # Add service status
    local first=true
    for service in "${!SERVICE_STATUS[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$status_file"
        fi
        echo "        \"$service\": \"${SERVICE_STATUS[$service]}\"" >> "$status_file"
    done
    
    cat >> "$status_file" << EOF
    }
}
EOF
}

# Initialize deployment with enhanced checks
initialize_deployment() {
    info_log "Initializing deployment..."
    
    # Check Python version
    check_python || return 1
    
    # Check PostgreSQL
    check_postgresql || return 1
    
    # Create required directories
    mkdir -p logs
    mkdir -p instance
    mkdir -p static/downloads
    
    # Set proper permissions
    chmod -R 755 static
    chmod +x *.py
    
    # Check .env file
    if [ ! -f ".env" ]; then
        info_log "Creating .env file from example..."
        cp .env.example .env
        echo -e "${YELLOW}Please update .env file with your configuration${NC}"
        read -p "Press Enter after updating .env file..."
    fi
    
    # Install screen if not present
    check_screen
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        info_log "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    fi
    
    success_log "Initialization complete"
}

# Start services
start_services() {
    info_log "Starting services..."
    
    # Start PostgreSQL
    systemctl start postgresql
    
    # Start Redis
    systemctl start redis-server
    
    # Start Nginx
    systemctl start nginx
    
    # Start Flask application in screen
    if ! check_screen_session ${SERVICE_SCREENS["flask"]}; then
        start_screen ${SERVICE_SCREENS["flask"]} "source venv/bin/activate && python app_final.py"
    fi
    
    # Start Terminal server in screen
    if ! check_screen_session ${SERVICE_SCREENS["terminal"]}; then
        start_screen ${SERVICE_SCREENS["terminal"]} "source venv/bin/activate && python terminal_server.py"
    fi
    
    success_log "All services started"
}

# Stop services
stop_services() {
    info_log "Stopping services..."
    
    # Stop screen sessions
    for screen_name in "${SERVICE_SCREENS[@]}"; do
        if check_screen_session $screen_name; then
            kill_screen $screen_name
        fi
    done
    
    # Stop system services
    systemctl stop nginx
    systemctl stop redis-server
    systemctl stop postgresql
    
    success_log "All services stopped"
}

# Enhanced monitoring with automatic restart
enhanced_monitor_services() {
    info_log "Starting enhanced service monitoring..."
    
    while [ "$MONITOR_RUNNING" = true ]; do
        clear
        echo -e "${CYAN}=== Terminusa Online Service Monitor ===${NC}"
        echo -e "Time: $(date '+%Y-%m-%d %H:%M:%S')\n"
        
        # System Resources
        echo -e "${YELLOW}System Resources:${NC}"
        echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
        echo "Memory Usage: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')"
        echo "Disk Usage: $(df -h / | awk 'NR==2{print $5}')"
        echo
        
        # Screen Sessions
        echo -e "${YELLOW}Screen Sessions:${NC}"
        screen -list | grep -v "There are screens" || echo "No active screens"
        echo
        
        # Service Status with Auto-Restart
        echo -e "${YELLOW}Service Status:${NC}"
        printf "%-15s %-10s %-20s %-20s\n" "Service" "Status" "Port" "Auto-Restart"
        echo "--------------------------------------------------------"
        
        for service in "${!SERVICE_PORTS[@]}"; do
            local status="stopped"
            local auto_restart="enabled"
            
            case $service in
                "postgresql"|"nginx"|"redis")
                    if systemctl is-active --quiet $service; then
                        status="running"
                    else
                        systemctl start $service
                    fi
                    ;;
                "flask"|"terminal")
                    if check_screen_session ${SERVICE_SCREENS[$service]}; then
                        status="running"
                    else
                        start_screen ${SERVICE_SCREENS[$service]} \
                            "source venv/bin/activate && python ${service}_server.py"
                    fi
                    ;;
            esac
            
            SERVICE_STATUS[$service]=$status
            
            if [ "$status" = "running" ]; then
                printf "%-15s ${GREEN}%-10s${NC} %-20s %-20s\n" \
                    "$service" "$status" "${SERVICE_PORTS[$service]}" "$auto_restart"
            else
                printf "%-15s ${RED}%-10s${NC} %-20s %-20s\n" \
                    "$service" "$status" "${SERVICE_PORTS[$service]}" "$auto_restart"
            fi
        done
        
        # Save status to JSON
        save_status
        
        sleep $MONITOR_INTERVAL
    done
}

# Show menu
show_menu() {
    while true; do
        clear
        echo -e "${CYAN}=== Terminusa Online Management ===${NC}"
        echo
        echo "1) Deploy/Update System"
        echo "2) Start All Services"
        echo "3) Stop All Services"
        echo "4) Restart All Services"
        echo "5) Enhanced Monitoring (with auto-restart)"
        echo "6) View Logs"
        echo "7) Database Operations"
        echo "8) Nginx Operations"
        echo "9) System Status"
        echo "10) Debug Mode"
        echo "0) Exit"
        echo
        read -p "Select an option: " choice
        
        case $choice in
            1)
                initialize_deployment
                ;;
            2)
                start_services
                ;;
            3)
                stop_services
                ;;
            4)
                stop_services
                sleep 2
                start_services
                ;;
            5)
                enhanced_monitor_services
                ;;
            6)
                echo -e "\n${YELLOW}Available Logs:${NC}"
                echo "1) Flask App Log"
                echo "2) Terminal Server Log"
                echo "3) Nginx Error Log"
                echo "4) Nginx Access Log"
                echo "5) PostgreSQL Log"
                echo "6) Redis Log"
                echo "7) Service Status Log"
                echo "0) Back to main menu"
                read -p "Select log to view: " log_choice
                case $log_choice in
                    1) tail -f logs/flask.log ;;
                    2) tail -f logs/terminal.log ;;
                    3) tail -f /var/log/nginx/error.log ;;
                    4) tail -f /var/log/nginx/access.log ;;
                    5) tail -f /var/log/postgresql/postgresql-main.log ;;
                    6) tail -f /var/log/redis/redis-server.log ;;
                    7) cat logs/service_status.json | python3 -m json.tool ;;
                    0) continue ;;
                    *) error_log "Invalid option" ;;
                esac
                ;;
            7)
                echo -e "\n${YELLOW}Database Operations:${NC}"
                echo "1) Backup Database"
                echo "2) Restore Database"
                echo "3) Run Migrations"
                echo "4) Initialize Database"
                echo "0) Back to main menu"
                read -p "Select operation: " db_choice
                case $db_choice in
                    1) 
                        backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
                        pg_dump -U terminusa terminusa_db > $backup_file
                        success_log "Database backed up to $backup_file"
                        ;;
                    2)
                        read -p "Enter backup file path: " restore_file
                        if [ -f "$restore_file" ]; then
                            psql -U terminusa terminusa_db < $restore_file
                            success_log "Database restored from $restore_file"
                        else
                            error_log "Backup file not found"
                        fi
                        ;;
                    3)
                        flask db upgrade
                        success_log "Database migrations completed"
                        ;;
                    4)
                        python init_database.py
                        success_log "Database initialized"
                        ;;
                    0) continue ;;
                    *) error_log "Invalid option" ;;
                esac
                ;;
            8)
                echo -e "\n${YELLOW}Nginx Operations:${NC}"
                echo "1) Test Configuration"
                echo "2) Reload Configuration"
                echo "3) View Active Sites"
                echo "0) Back to main menu"
                read -p "Select operation: " nginx_choice
                case $nginx_choice in
                    1) nginx -t ;;
                    2) systemctl reload nginx ;;
                    3) ls -l /etc/nginx/sites-enabled/ ;;
                    0) continue ;;
                    *) error_log "Invalid option" ;;
                esac
                ;;
            9)
                cat logs/service_status.json | python3 -m json.tool
                ;;
            10)
                if [ "$DEBUG" = true ]; then
                    DEBUG=false
                    info_log "Debug mode disabled"
                else
                    DEBUG=true
                    info_log "Debug mode enabled"
                fi
                ;;
            0)
                info_log "Exiting..."
                exit 0
                ;;
            *)
                error_log "Invalid option"
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Trap signals for graceful shutdown
trap 'MONITOR_RUNNING=false; stop_services; exit 0' SIGINT SIGTERM

# Main execution
mkdir -p logs
show_menu
