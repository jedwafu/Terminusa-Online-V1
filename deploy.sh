#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Production deployment configuration
PROD_SERVER="46.250.228.210"
PROD_USER="root"
APP_DIR="/var/www/terminusa"
BACKUP_DIR="/var/www/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
WEB_ROOT="/var/www/terminusa"
STATIC_DIR="$WEB_ROOT/static"

# Debug mode flag
DEBUG=false

# Error handling
set -e
trap 'echo -e "${RED}Deployment failed${NC}"; exit 1' ERR

# Service configurations
declare -A SERVICE_PORTS=(
    ["postgresql"]="5432"
    ["nginx"]="80,443"
    ["flask"]="5000"
    ["terminal"]="6789"
    ["redis"]="6379"
    ["postfix"]="25"
    ["game"]="5001"
)

declare -A SERVICE_LOGS=(
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

declare -A SERVICE_SCREENS=(
    ["flask"]="terminusa-flask"
    ["terminal"]="terminusa-terminal"
    ["game"]="terminusa-game"
    ["email_monitor"]="terminusa-email"
    ["ai_manager"]="terminusa-ai"
    ["combat_manager"]="terminusa-combat"
    ["economy_systems"]="terminusa-economy"
    ["game_mechanics"]="terminusa-mechanics"
)

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Enhanced setup_static_files with better error handling
setup_static_files() {
    info_log "Setting up static files..."
    
    # Create required directories
    sudo mkdir -p $STATIC_DIR/{css,js,images}
    
    # Copy static files with error checking
    info_log "Copying static files..."
    if [ -d "static" ]; then
        sudo cp -r static/* $STATIC_DIR/ 2>/dev/null || {
            error_log "Failed to copy static files"
            return 1
        }
    else
        error_log "Static directory not found!"
        return 1
    fi
    
    # Set permissions
    info_log "Setting permissions..."
    sudo chown -R www-data:www-data $WEB_ROOT
    sudo chmod -R 755 $WEB_ROOT
    
    # Create symbolic links
    info_log "Creating symbolic links..."
    sudo ln -sf $STATIC_DIR /root/Terminusa/static
    
    # Verify nginx configuration
    info_log "Verifying nginx configuration..."
    if ! sudo nginx -t; then
        error_log "Nginx configuration test failed!"
        return 1
    fi
    
    success_log "Static files setup completed"
    return 0
}

# Enhanced database setup
setup_database() {
    info_log "Setting up database..."
    
    # Check if PostgreSQL is running
    if ! systemctl is-active --quiet postgresql; then
        error_log "PostgreSQL is not running!"
        return 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Set environment variables
    export FLASK_APP=init_db.py
    export PYTHONPATH=$PWD
    
    # Initialize database
    info_log "Initializing database..."
    python init_db.py || {
        error_log "Database initialization failed!"
        return 1
    }
    
    # Run migrations
    info_log "Running database migrations..."
    if [ ! -d "migrations" ]; then
        flask db init || {
            error_log "Migration initialization failed!"
            return 1
        }
    fi
    
    # Stamp the database with the current head
    flask db stamp head || {
        error_log "Migration stamp failed!"
        return 1
    }
    
    # Create new migration
    flask db migrate -m "Database update $(date +%Y%m%d_%H%M%S)" || {
        error_log "Migration creation failed!"
        return 1
    }
    
    # Apply migrations
    flask db upgrade || {
        error_log "Migration upgrade failed!"
        return 1
    }
    
    success_log "Database setup completed"
    return 0
}

# Enhanced nginx setup
setup_nginx() {
    info_log "Setting up nginx..."
    
    # Update nginx user
    sudo sed -i 's/user root/user www-data/' /etc/nginx/nginx.conf
    
    # Copy nginx configuration
    sudo cp nginx/terminusa.conf /etc/nginx/sites-available/
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/terminusa.conf /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    if ! sudo nginx -t; then
        error_log "Nginx configuration test failed!"
        return 1
    fi
    
    # Restart nginx
    sudo systemctl restart nginx
    
    success_log "Nginx setup completed"
    return 0
}

# Stop services
stop_services() {
    info_log "Stopping services..."
    
    # Kill all screen sessions first
    info_log "Stopping screen sessions..."
    for service in "${!SERVICE_SCREENS[@]}"; do
        screen_name=${SERVICE_SCREENS[$service]}
        if check_screen_session "$screen_name"; then
            info_log "Killing screen session: $screen_name"
            kill_screen "$screen_name"
        fi
    done
    
    # Stop system services
    info_log "Stopping system services..."
    systemctl stop nginx
    systemctl stop redis-server
    systemctl stop postgresql
    systemctl stop postfix
    
    # Kill any processes on our ports
    for service in "${!SERVICE_PORTS[@]}"; do
        IFS=',' read -ra PORTS <<< "${SERVICE_PORTS[$service]}"
        for port in "${PORTS[@]}"; do
            if check_port $port; then
                info_log "Killing process on port $port..."
                kill_port_process $port
            fi
        done
    done
    
    success_log "All services stopped"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    netstat -tuln | grep -q ":$port "
    return $?
}

# Function to kill process on a port
kill_port_process() {
    local port=$1
    local pid=$(lsof -t -i:$port)
    if [ ! -z "$pid" ]; then
        kill -9 $pid 2>/dev/null
    fi
}

# Screen management functions
check_screen() {
    if ! command -v screen &> /dev/null; then
        info_log "Installing screen..."
        apt-get update && apt-get install -y screen
    fi
}

start_screen() {
    local name=$1
    local command=$2
    screen -dmS $name bash -c "$command"
}

check_screen_session() {
    local name=$1
    screen -list | grep -q "$name"
}

kill_screen() {
    local name=$1
    screen -X -S $name quit >/dev/null 2>&1
}

# Enhanced service management
start_services() {
    info_log "Starting services..."
    
    # Check if screen is installed
    check_screen
    
    # Create logs directory
    mkdir -p logs
    
    # Start system services
    systemctl start postgresql
    systemctl start redis-server
    systemctl start nginx
    systemctl start postfix
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Start application services in screen sessions
    for service in "${!SERVICE_SCREENS[@]}"; do
        screen_name=${SERVICE_SCREENS[$service]}
        if ! screen -list | grep -q "$screen_name"; then
            case $service in
                "flask")
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python app.py > logs/flask.log 2>&1"
                    ;;
                "terminal")
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python terminal_server.py > logs/terminal.log 2>&1"
                    ;;
                "game")
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python game_server.py > logs/game.log 2>&1"
                    ;;
                *)
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python ${service}.py > logs/${service}.log 2>&1"
                    ;;
            esac
        fi
    done
    
    # Wait for services to start
    sleep 5
    
    # Check service status
    show_system_status
    
    success_log "All services started"
}

# Enhanced system status monitoring
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
    
    # Check system services
    for service in postgresql redis-server nginx postfix; do
        if systemctl is-active --quiet $service; then
            printf "%-20s ${GREEN}%-10s${NC} %-20s\n" "$service" "Running" "${SERVICE_PORTS[$service]}"
        else
            printf "%-20s ${RED}%-10s${NC} %-20s\n" "$service" "Stopped" "-"
        fi
    done
    
    # Check screen services
    for service in "${!SERVICE_SCREENS[@]}"; do
        screen_name=${SERVICE_SCREENS[$service]}
        if screen -list | grep -q "$screen_name"; then
            printf "%-20s ${GREEN}%-10s${NC} %-20s\n" "$service" "Running" "${SERVICE_PORTS[$service]:-"-"}"
        else
            printf "%-20s ${RED}%-10s${NC} %-20s\n" "$service" "Stopped" "-"
        fi
    done
    
    echo
    echo -e "${YELLOW}Screen Sessions:${NC}"
    screen -list | grep -v "There are screens" || echo "No active screens"
    
    # Save status to JSON
    save_status_json
}

# Enhanced production deployment
deploy_production() {
    info_log "Preparing for production deployment..."
    
    # Create backup
    ssh $PROD_USER@$PROD_SERVER "mkdir -p $BACKUP_DIR"
    ssh $PROD_USER@$PROD_SERVER "if [ -d $APP_DIR ]; then tar -czf $BACKUP_DIR/terminusa_$TIMESTAMP.tar.gz -C $APP_DIR .; fi"
    
    # Create deployment package
    info_log "Creating deployment package..."
    tar -czf deploy.tar.gz \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='.env' \
        --exclude='node_modules' \
        --exclude='tests' \
        --exclude='*.log' \
        .
    
    # Upload and deploy
    scp deploy.tar.gz $PROD_USER@$PROD_SERVER:/tmp/
    ssh $PROD_USER@$PROD_SERVER "
        systemctl stop terminusa terminusa-terminal
        rm -rf $APP_DIR/*
        mkdir -p $APP_DIR
        tar -xzf /tmp/deploy.tar.gz -C $APP_DIR
        chown -R www-data:www-data $APP_DIR
        chmod -R 755 $APP_DIR
        cd $APP_DIR
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        flask db upgrade
        systemctl start terminusa terminusa-terminal
        rm /tmp/deploy.tar.gz
    "
    
    # Verify deployment
    info_log "Verifying deployment..."
    curl -s https://terminusa.online/health | grep -q "ok" && \
        success_log "Main website is up" || \
        error_log "Main website verification failed"
    
    curl -s https://play.terminusa.online/health | grep -q "ok" && \
        success_log "Game server is up" || \
        error_log "Game server verification failed"
    
    # Cleanup
    rm deploy.tar.gz
    
    success_log "Production deployment completed"
}

# Main menu
show_menu() {
    while true; do
        clear
        echo -e "${CYAN}=== Terminusa Online Management ===${NC}"
        echo
        echo "1) Initialize/Update System"
        echo "2) Start All Services"
        echo "3) Stop All Services"
        echo "4) Restart All Services"
        echo "5) View System Status"
        echo "6) View Logs"
        echo "7) Database Operations"
        echo "8) Deploy to Production"
        echo "9) Debug Mode"
        echo "0) Exit"
        echo
        read -p "Select an option: " choice
        
        case $choice in
            1)
                setup_static_files && setup_database && setup_nginx
                ;;
            2)
                start_services
                ;;
            3)
                stop_services
                ;;
            4)
                stop_services && sleep 2 && start_services
                ;;
            5)
                show_system_status
                ;;
            6)
                show_logs_menu
                ;;
            7)
                show_database_menu
                ;;
            8)
                deploy_production
                ;;
            9)
                DEBUG=$([[ "$DEBUG" == "true" ]] && echo "false" || echo "true")
                info_log "Debug mode: $DEBUG"
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

# Initialize
mkdir -p logs
show_menu
