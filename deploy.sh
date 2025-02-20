#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Debug mode flag
DEBUG=false

# Monitor interval
MONITOR_INTERVAL=5

# Monitor running flag
MONITOR_RUNNING=false

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
    ["postfix"]="25"
    ["game"]="5001"
)

SERVICE_LOGS=(
    ["postgresql"]="/var/log/postgresql/postgresql-main.log"
    ["nginx"]="/var/log/nginx/error.log"
    ["flask"]="logs/flask.log"
    ["terminal"]="logs/terminal.log"
    ["redis"]="/var/log/redis/redis-server.log"
    ["postfix"]="/var/log/mail.log"
    ["game"]="logs/game.log"
    ["email_monitor"]="logs/email_monitor.log"
    ["ai_manager"]="logs/ai_manager.log"
    ["combat_manager"]="logs/combat_manager.log"
    ["economy_systems"]="logs/economy_systems.log"
    ["game_mechanics"]="logs/game_mechanics.log"
)

SERVICE_SCREENS=(
    ["flask"]="terminusa-flask"
    ["terminal"]="terminusa-terminal"
    ["game"]="terminusa-game"
    ["email_monitor"]="terminusa-email"
    ["ai_manager"]="terminusa-ai"
    ["combat_manager"]="terminusa-combat"
    ["economy_systems"]="terminusa-economy"
    ["game_mechanics"]="terminusa-mechanics"
)

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

# Check if port is in use
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Kill process using port
kill_port_process() {
    local port=$1
    local pid=$(lsof -t -i:$port)
    if [ ! -z "$pid" ]; then
        info_log "Port $port is in use by PID $pid. Stopping process..."
        kill -15 $pid
        sleep 2
        if kill -0 $pid 2>/dev/null; then
            kill -9 $pid
            sleep 1
        fi
    fi
}

# Show port status
show_port_status() {
    local port=$1
    info_log "Checking port $port..."
    if check_port $port; then
        pid=$(lsof -t -i:$port)
        process=$(ps -p $pid -o comm=)
        error_log "Port $port is in use by process $process (PID: $pid)"
        lsof -i :$port
    else
        success_log "Port $port is free"
    fi
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

# Initialize deployment
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
    mkdir -p data/{market,combat,social,ai}
    
    # Set proper permissions
    chmod -R 755 static
    chmod +x *.py
    chmod +x scripts/*.py
    chmod +x *.sh
    
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

# Stop services
stop_services() {
    info_log "Stopping services..."
    
    # Kill all screen sessions first
    info_log "Stopping screen sessions..."
    for screen_name in "${SERVICE_SCREENS[@]}"; do
        if check_screen_session $screen_name; then
            info_log "Stopping screen session: $screen_name"
            kill_screen $screen_name
        fi
    done

    # Stop system services
    info_log "Stopping system services..."
    systemctl stop nginx
    systemctl stop redis-server
    systemctl stop postgresql
    systemctl stop postfix
    
    success_log "All services stopped"
}

# Show menu function
show_menu() {
    while true; do
        clear
        echo -e "${CYAN}=== Terminusa Online Management ===${NC}"
        echo
        echo "1) Deploy/Update System"
        echo "2) Start All Services"
        echo "3) Stop All Services"
        echo "4) Restart All Services"
        echo "5) Enhanced Monitoring"
        echo "6) View Logs"
        echo "7) Database Operations"
        echo "8) Game Systems"
        echo "9) System Status"
        echo "10) Port Management"
        echo "11) Debug Mode"
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
                echo "3) Game Server Log"
                echo "4) Email Monitor Log"
                echo "5) AI Manager Log"
                echo "6) Combat Manager Log"
                echo "7) Economy Systems Log"
                echo "8) Game Mechanics Log"
                echo "9) Nginx Error Log"
                echo "10) Nginx Access Log"
                echo "11) PostgreSQL Log"
                echo "12) Redis Log"
                echo "13) Service Status Log"
                echo "0) Back to main menu"
                read -p "Select log to view: " log_choice
                case $log_choice in
                    1) tail -f logs/flask.log ;;
                    2) tail -f logs/terminal.log ;;
                    3) tail -f logs/game.log ;;
                    4) tail -f logs/email_monitor.log ;;
                    5) tail -f logs/ai_manager.log ;;
                    6) tail -f logs/combat_manager.log ;;
                    7) tail -f logs/economy_systems.log ;;
                    8) tail -f logs/game_mechanics.log ;;
                    9) tail -f /var/log/nginx/error.log ;;
                    10) tail -f /var/log/nginx/access.log ;;
                    11) tail -f /var/log/postgresql/postgresql-main.log ;;
                    12) tail -f /var/log/redis/redis-server.log ;;
                    13) cat logs/service_status.json | python3 -m json.tool ;;
                    0) continue ;;
                    *) error_log "Invalid option" ;;
                esac
                read -p "Press Enter to return to the previous menu..."
                ;;
            7)
                # Database operations code...
                ;;
            8)
                # Game systems code...
                ;;
            9)
                # System status code...
                ;;
            10)
                # Port management code...
                ;;
            11)
                # Debug mode code...
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
