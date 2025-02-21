#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# Create logs directory
mkdir -p logs

# Load environment variables
if [ -f .env ]; then
    # Load env vars but skip comments and handle special characters
    set -a
    source .env
    set +a
else
    error_log ".env file not found"
    exit 1
fi

# Set timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Verify required environment variables
required_vars=(
    "PROD_SERVER"
    "PROD_USER"
    "MAIN_APP_DIR"
    "MAIN_STATIC_DIR"
    "GAME_APP_DIR"
    "GAME_STATIC_DIR"
    "BACKUP_DIR"
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error_log "Required environment variable $var is not set"
        exit 1
    fi
done

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
    
    # Setup static files
    info_log "Setting up static files..."
    
    # Create directories
    sudo mkdir -p $MAIN_STATIC_DIR/{css,js,images}
    sudo mkdir -p $GAME_STATIC_DIR/{css,js,images}
    
    # Copy static files
    if [ -d "static" ]; then
        # Copy to main website
        sudo cp -r static/* $MAIN_STATIC_DIR/ 2>/dev/null || {
            error_log "Failed to copy static files to main website"
            return 1
        }
        
        # Copy to game application
        sudo cp -r static/* $GAME_STATIC_DIR/ 2>/dev/null || {
            error_log "Failed to copy static files to game application"
            return 1
        }
    else
        error_log "Static directory not found!"
        return 1
    fi
    
    # Set permissions
    sudo chown -R www-data:www-data $MAIN_APP_DIR
    sudo chmod -R 755 $MAIN_APP_DIR
    sudo chown -R www-data:www-data $GAME_APP_DIR
    sudo chmod -R 755 $GAME_APP_DIR
    
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
    
    # Create backups
    ssh $PROD_USER@$PROD_SERVER "mkdir -p $BACKUP_DIR"
    ssh $PROD_USER@$PROD_SERVER "
        if [ -d $MAIN_APP_DIR ]; then 
            tar -czf $BACKUP_DIR/terminusa-web_$TIMESTAMP.tar.gz -C $MAIN_APP_DIR .;
        fi;
        if [ -d $GAME_APP_DIR ]; then 
            tar -czf $BACKUP_DIR/terminusa-game_$TIMESTAMP.tar.gz -C $GAME_APP_DIR .;
        fi
    "
    
    # Create deployment packages
    info_log "Creating deployment packages..."
    
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
    info_log "Uploading deployment package..."
    scp deploy.tar.gz $PROD_USER@$PROD_SERVER:/tmp/
    
    info_log "Deploying to main website directory..."
    ssh $PROD_USER@$PROD_SERVER "
        systemctl stop terminusa-web
        rm -rf $MAIN_APP_DIR/*
        mkdir -p $MAIN_APP_DIR
        cd $MAIN_APP_DIR
        tar -xzf /tmp/deploy.tar.gz
        chown -R www-data:www-data .
        chmod -R 755 .
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        flask db upgrade
        systemctl start terminusa-web
    "
    
    info_log "Deploying to game application directory..."
    ssh $PROD_USER@$PROD_SERVER "
        systemctl stop terminusa-game terminusa-terminal
        rm -rf $GAME_APP_DIR/*
        mkdir -p $GAME_APP_DIR
        cd $GAME_APP_DIR
        tar -xzf /tmp/deploy.tar.gz
        chown -R www-data:www-data .
        chmod -R 755 .
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        flask db upgrade
        systemctl start terminusa-game terminusa-terminal
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
    
    # Cleanup local files
    rm -f deploy.tar.gz
    
    success_log "Production deployment completed successfully"
}

# Show logs menu
show_logs_menu() {
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
        0) return ;;
        *) error_log "Invalid option" ;;
    esac
}

# Show database menu
show_database_menu() {
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
            info_log "Creating database backup: $backup_file"
            PGPASSWORD=${POSTGRES_PASSWORD} pg_dump -h localhost -U ${POSTGRES_USER} ${POSTGRES_DB} > $backup_file
            if [ $? -eq 0 ]; then
                success_log "Database backed up to $backup_file"
            else
                error_log "Database backup failed"
            fi
            ;;
        2)
            read -p "Enter backup file path: " restore_file
            if [ -f "$restore_file" ]; then
                info_log "Restoring database from: $restore_file"
                PGPASSWORD=${POSTGRES_PASSWORD} psql -h localhost -U ${POSTGRES_USER} ${POSTGRES_DB} < $restore_file
                if [ $? -eq 0 ]; then
                    success_log "Database restored from $restore_file"
                else
                    error_log "Database restore failed"
                fi
            else
                error_log "Backup file not found"
            fi
            ;;
        3)
            info_log "Running database migrations"
            source venv/bin/activate
            flask db stamp head  # Reset migration head
            flask db migrate     # Generate new migrations
            flask db upgrade     # Apply migrations
            success_log "Database migrations completed"
            ;;
        4)
            info_log "Initializing database"
            source venv/bin/activate
            # Create database if it doesn't exist
            PGPASSWORD=${POSTGRES_PASSWORD} psql -h localhost -U ${POSTGRES_USER} -d postgres -c "CREATE DATABASE ${POSTGRES_DB};" 2>/dev/null || true
            # Initialize database schema
            python init_db.py
            if [ $? -eq 0 ]; then
                success_log "Database initialized successfully"
            else
                error_log "Database initialization failed"
            fi
            ;;
        0) return ;;
        *) error_log "Invalid option" ;;
    esac
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
