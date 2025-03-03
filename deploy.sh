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

# Service configurations
declare -A SERVICE_PORTS=(
    ["postgresql"]="5432"
    ["nginx"]="80,443"
    ["flask"]="5000"
    ["terminal"]="6789"
    ["redis"]="6379"
    ["postfix"]="25"
    ["game"]="5001"
    ["currency"]="5002"
    ["marketplace"]="5003"
    ["gacha"]="5004"
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
    ["currency"]="logs/currency.log"
    ["marketplace"]="logs/marketplace.log"
    ["gacha"]="logs/gacha.log"
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
    ["currency"]="terminusa-currency"
    ["marketplace"]="terminusa-marketplace"
    ["gacha"]="terminusa-gacha"
)

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
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python web_app.py > logs/flask.log 2>&1"
                    ;;
                "terminal")
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python terminal_server.py > logs/terminal.log 2>&1"
                    ;;
                "game")
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python game_server.py > logs/game.log 2>&1"
                    ;;
                "currency")
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python currency_system.py > logs/currency.log 2>&1"
                    ;;
                "marketplace")
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python marketplace_system.py > logs/marketplace.log 2>&1"
                    ;;
                "gacha")
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python gacha_system.py > logs/gacha.log 2>&1"
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
    echo "13) Mail Log"
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
        13) tail -f /var/log/mail.log ;;
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
            flask db upgrade
            success_log "Database migrations completed"
            ;;
        4)
            info_log "Initializing database"
            source venv/bin/activate
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
                info_log "Initializing system..."
                
                # Create terminusa user if it doesn't exist
                if ! id -u terminusa >/dev/null 2>&1; then
                    info_log "Creating terminusa user..."
                    sudo useradd -r -s /bin/false terminusa
                fi

                # Create necessary directories with proper permissions
                info_log "Creating directories..."
                sudo mkdir -p /var/www/terminusa
                sudo mkdir -p /var/log/terminusa
                sudo mkdir -p static/css static/js static/fonts
                sudo mkdir -p templates
                
                # Set proper ownership and permissions
                sudo chown -R terminusa:terminusa /var/www/terminusa
                sudo chown -R terminusa:terminusa /var/log/terminusa
                sudo chown -R terminusa:terminusa static templates
                sudo chmod -R 755 /var/www/terminusa
                sudo chmod -R 755 /var/log/terminusa
                sudo chmod -R 755 static templates

                # Install systemd service
                info_log "Installing systemd service..."
                if [ -f services/terminusa-terminal.service ]; then
                    sudo cp services/terminusa-terminal.service /etc/systemd/system/
                    sudo systemctl daemon-reload
                    sudo systemctl enable terminusa-terminal.service
                    success_log "Systemd service installed"
                else
                    error_log "Service file not found in services directory"
                    read -p "Press Enter to continue..."
                    return 1
                fi

                # Install system dependencies
                info_log "Installing system dependencies..."
                if ! command -v npm &> /dev/null || ! command -v node &> /dev/null; then
                    info_log "Installing Node.js and npm..."
                    if [ -f /etc/debian_version ]; then
                        # Debian/Ubuntu
                        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
                        sudo apt-get install -y nodejs build-essential
                    elif [ -f /etc/redhat-release ]; then
                        # RHEL/CentOS
                        curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo -E bash -
                        sudo yum install -y nodejs gcc-c++ make
                    else
                        error_log "Unsupported distribution"
                        read -p "Press Enter to continue..."
                        return 1
                    fi
                    
                    if ! command -v npm &> /dev/null; then
                        error_log "Failed to install npm"
                        read -p "Press Enter to continue..."
                        return 1
                    fi
                    success_log "Node.js and npm installed successfully"
                else
                    success_log "Node.js and npm are already installed"
                fi

                # Set up terminusa user with proper home directory
                info_log "Setting up terminusa user..."
                if ! id -u terminusa >/dev/null 2>&1; then
                    sudo useradd -m -d /home/terminusa -s /bin/bash terminusa
                fi

                # Set up project directories
                info_log "Setting up directories..."
                sudo mkdir -p /var/www/terminusa/{static,templates,logs}
                sudo mkdir -p /home/terminusa/.npm
                sudo mkdir -p client/node_modules
                sudo mkdir -p logs

                # Set proper ownership and permissions
                info_log "Setting permissions..."
                sudo chown -R terminusa:terminusa /var/www/terminusa
                sudo chown -R terminusa:terminusa /home/terminusa
                sudo chown -R terminusa:terminusa client
                sudo chown -R terminusa:terminusa logs
                sudo chmod -R 755 /var/www/terminusa
                sudo chmod -R 755 /home/terminusa
                sudo chmod -R 755 client
                sudo chmod -R 755 logs

                # Make setup script executable
                info_log "Running static files setup..."
                chmod +x setup_static_files.sh

                # Install Node.js and npm
                info_log "Installing Node.js and npm..."
                if ! command -v node > /dev/null || ! command -v npm > /dev/null; then
                    sudo apt-get update
                    sudo apt-get install -y nodejs npm build-essential
                fi

                # Set up directories
                info_log "Setting up directories..."
                INSTALL_DIR="/var/www/terminusa"
                sudo mkdir -p "$INSTALL_DIR"
                sudo mkdir -p /home/terminusa

                # Copy files
                info_log "Copying files..."
                sudo cp -r . "$INSTALL_DIR/"

                # Set permissions
                info_log "Setting permissions..."
                sudo chown -R terminusa:terminusa "$INSTALL_DIR"
                sudo chown -R terminusa:terminusa /home/terminusa
                sudo chmod +x "$INSTALL_DIR/setup_static_files.sh"

                # Run setup script
                info_log "Running setup script..."
                if sudo -u terminusa bash -c "cd $INSTALL_DIR && HOME=/home/terminusa ./setup_static_files.sh"; then
                    success_log "Static files setup completed"
                else
                    error_log "Static files setup failed"
                    read -p "Press Enter to continue..."
                    return 1
                fi
                
                # Setup database
                info_log "Setting up database..."
                source venv/bin/activate
                if python init_db.py; then
                    success_log "Database setup completed"
                else
                    error_log "Database setup failed"
                    read -p "Press Enter to continue..."
                    return 1
                fi
                
                # Setup nginx
                info_log "Setting up nginx..."
                if [ -f /etc/nginx/sites-available/terminusa ]; then
                    success_log "Nginx already configured"
                else
                    sudo cp nginx/terminusa.conf /etc/nginx/sites-available/terminusa
                    sudo ln -sf /etc/nginx/sites-available/terminusa /etc/nginx/sites-enabled/
                    sudo nginx -t && sudo systemctl restart nginx
                    success_log "Nginx setup completed"
                fi
                
                success_log "System initialization completed"
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
