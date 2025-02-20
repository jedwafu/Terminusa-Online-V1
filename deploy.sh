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

# Get service resource usage
get_service_resources() {
    local service=$1
    local pid=${SERVICE_PIDS[$service]}
    
    if [ ! -z "$pid" ] && ps -p $pid >/dev/null 2>&1; then
        local cpu=$(ps -p $pid -o %cpu | tail -n 1)
        local mem=$(ps -p $pid -o %mem | tail -n 1)
        local vsz=$(ps -p $pid -o vsz | tail -n 1)
        echo "$cpu $mem $vsz"
    else
        echo "0 0 0"
    fi
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

# Initialize deployment
initialize_deployment() {
    info_log "Initializing deployment..."
    
    # Create required directories
    mkdir -p logs
    mkdir -p instance
    mkdir -p static/downloads
    
    # Set proper permissions
    chmod -R 755 static
    chmod +x *.py
    
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

# Monitor services
monitor_services() {
    clear
    echo -e "${CYAN}=== Terminusa Online Service Monitor ===${NC}"
    echo -e "Press Ctrl+C to exit monitoring\n"
    
    while true; do
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
        
        # Service Status
        echo -e "${YELLOW}Service Status:${NC}"
        printf "%-15s %-10s %-20s\n" "Service" "Status" "Port"
        echo "----------------------------------------"
        
        # Check PostgreSQL
        if systemctl is-active --quiet postgresql; then
            printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "PostgreSQL" "Running" "${SERVICE_PORTS["postgresql"]}"
        else
            printf "%-15s ${RED}%-10s${NC} %-20s\n" "PostgreSQL" "Stopped" "-"
        fi
        
        # Check Redis
        if systemctl is-active --quiet redis-server; then
            printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "Redis" "Running" "${SERVICE_PORTS["redis"]}"
        else
            printf "%-15s ${RED}%-10s${NC} %-20s\n" "Redis" "Stopped" "-"
        fi
        
        # Check Nginx
        if systemctl is-active --quiet nginx; then
            printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "Nginx" "Running" "${SERVICE_PORTS["nginx"]}"
        else
            printf "%-15s ${RED}%-10s${NC} %-20s\n" "Nginx" "Stopped" "-"
        fi
        
        # Check Flask app
        if check_screen_session ${SERVICE_SCREENS["flask"]}; then
            printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "Flask App" "Running" "${SERVICE_PORTS["flask"]}"
        else
            printf "%-15s ${RED}%-10s${NC} %-20s\n" "Flask App" "Stopped" "-"
        fi
        
        # Check Terminal server
        if check_screen_session ${SERVICE_SCREENS["terminal"]}; then
            printf "%-15s ${GREEN}%-10s${NC} %-20s\n" "Terminal" "Running" "${SERVICE_PORTS["terminal"]}"
        else
            printf "%-15s ${RED}%-10s${NC} %-20s\n" "Terminal" "Stopped" "-"
        fi
        
        sleep 5
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
        echo "5) Monitor Services"
        echo "6) View Logs"
        echo "7) Database Operations"
        echo "8) Nginx Operations"
        echo "9) Debug Mode"
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
                monitor_services
                ;;
            6)
                echo -e "\n${YELLOW}Available Logs:${NC}"
                echo "1) Flask App Log"
                echo "2) Terminal Server Log"
                echo "3) Nginx Error Log"
                echo "4) Nginx Access Log"
                echo "5) PostgreSQL Log"
                echo "6) Redis Log"
                echo "0) Back to main menu"
                read -p "Select log to view: " log_choice
                case $log_choice in
                    1) tail -f logs/flask.log ;;
                    2) tail -f logs/terminal.log ;;
                    3) tail -f /var/log/nginx/error.log ;;
                    4) tail -f /var/log/nginx/access.log ;;
                    5) tail -f /var/log/postgresql/postgresql-main.log ;;
                    6) tail -f /var/log/redis/redis-server.log ;;
                    0) continue ;;
                    *) error_log "Invalid option" ;;
                esac
                ;;
            7)
                echo -e "\n${YELLOW}Database Operations:${NC}"
                echo "1) Backup Database"
                echo "2) Restore Database"
                echo "3) Run Migrations"
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

# Main execution
mkdir -p logs
show_menu
