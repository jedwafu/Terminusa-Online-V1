#!/bin/bash
# Improved deploy.sh script for Terminusa Online
# This script manages deployment, service control, and system setup

# Enable error handling
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Debug mode flag (default: false)
DEBUG=false

# Script variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${SCRIPT_DIR}/backups"

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

# Function to check if script is run with sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        error_log "This operation requires sudo privileges. Please run with sudo."
        return 1
    fi
    return 0
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Create logs directory
mkdir -p logs
mkdir -p "$BACKUP_DIR"

# Load environment variables
if [ -f .env ]; then
    # Load env vars but skip comments and handle special characters
    set -a
    source .env
    set +a
    success_log "Environment variables loaded from .env"
else
    error_log ".env file not found"
    info_log "Creating sample .env file"
    cat > .env << EOF
# Terminusa Online Environment Configuration

# Server Configuration
PROD_SERVER=your-server.com
PROD_USER=terminusa
MAIN_APP_DIR=/var/www/terminusa
MAIN_STATIC_DIR=/var/www/terminusa/static
GAME_APP_DIR=/var/www/terminusa/game
GAME_STATIC_DIR=/var/www/terminusa/game/static
BACKUP_DIR=/var/www/terminusa/backups

# Port Configuration
WEBAPP_PORT=3000
API_PORT=5000
TERMINAL_PORT=6789

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/terminusa
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=terminusa

# Security
FLASK_SECRET_KEY=generate_a_secure_random_key
JWT_SECRET_KEY=generate_another_secure_random_key
SECURITY_PASSWORD_SALT=generate_a_secure_salt

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@terminusa.online

# Web3 Configuration
SOLANA_NETWORK=mainnet
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
EXON_CONTRACT_ADDRESS=your_contract_address

# Feature Flags
ENABLE_WEB3=True
ENABLE_GACHA=True
ENABLE_TRADING=True
ENABLE_GAMBLING=True
ENABLE_REFERRALS=True
ENABLE_LOYALTY=True
ENABLE_GUILD_QUESTS=True
EOF
    error_log "Please edit the .env file with your configuration and run the script again"
    exit 1
fi

# Verify required environment variables
# Set default port values if not defined in .env
WEBAPP_PORT=${WEBAPP_PORT:-3000}
API_PORT=${API_PORT:-5000}
TERMINAL_PORT=${TERMINAL_PORT:-6789}

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

missing_vars=0
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error_log "Required environment variable $var is not set"
        missing_vars=$((missing_vars+1))
    fi
done

if [ $missing_vars -gt 0 ]; then
    error_log "$missing_vars required environment variables are missing. Please check your .env file."
    exit 1
fi

# Service configurations
declare -A SERVICE_PORTS=(
    ["postgresql"]="5432"
    ["nginx"]="80,443"
    ["flask"]="${API_PORT}"
    ["webapp"]="${WEBAPP_PORT}"
    ["terminal"]="${TERMINAL_PORT}"
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
    ["webapp"]="logs/web.log"
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
    ["webapp"]="terminusa-webapp"
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

# Function to check and fix Flask-Login initialization in web_app.py
check_and_fix_webapp() {
    info_log "Checking web_app.py for Flask-Login initialization..."
    
    if [ -f "web_app.py" ]; then
        # Check if Flask-Login is imported but not initialized
        if grep -q "from flask_login import" web_app.py && ! grep -q "login_manager = LoginManager(app)" web_app.py; then
            info_log "Flask-Login is imported but not initialized in web_app.py. Fixing..."
            
            # Create a backup of the original file
            cp web_app.py web_app.py.bak.${TIMESTAMP}
            success_log "Created backup of web_app.py at web_app.py.bak.${TIMESTAMP}"
            
            # Add Flask-Login initialization
            sed -i '/from flask_jwt_extended import/a from flask_login import LoginManager, current_user' web_app.py
            sed -i '/jwt = JWTManager(app)/a \    # Initialize Flask-Login\n    login_manager = LoginManager(app)\n    login_manager.login_view = "login_page"\n\n    @login_manager.user_loader\n    def load_user(user_id):\n        return User.query.get(int(user_id))' web_app.py
            
            success_log "Fixed Flask-Login initialization in web_app.py"
        else
            success_log "Flask-Login is properly initialized in web_app.py or not used"
        fi
    else
        error_log "web_app.py not found"
    fi
}

# Function to check and create web_app_simple.py if it doesn't exist
check_and_create_simple_webapp() {
    info_log "Checking for web_app_simple.py..."
    
    if [ ! -f "web_app_simple.py" ]; then
        info_log "web_app_simple.py not found. Creating a simplified version..."
        
        cat > web_app_simple.py << EOF
from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            static_url_path='/static',
            static_folder='static')

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', title='Home')

@app.route('/play')
def play_page():
    """Play page"""
    return redirect('https://play.terminusa.online')

@app.route('/login')
def login_page():
    """Login page"""
    try:
        return render_template('login_new.html', 
                             title='Login',
                             is_authenticated=False)
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        return render_template('error.html', 
                             error_message='An error occurred while loading the page. Please try again later.'), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('error.html', 
                         error_message='The page you are looking for could not be found.'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', 
                         error_message='An internal server error occurred. Please try again later.'), 500

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('WEBAPP_PORT', 3000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug)
EOF
        
        success_log "Created web_app_simple.py"
    else
        success_log "web_app_simple.py already exists"
    fi
}

# Function to check and fix base.html template
check_and_fix_base_html() {
    info_log "Checking base.html for invalid endpoints..."
    
    if [ -f "templates/base.html" ]; then
        # Check if the swapper endpoint is referenced
        if grep -q 'url_for.*pages.swapper' templates/base.html; then
            info_log "Found reference to non-existent endpoint 'pages.swapper' in base.html. Fixing..."
            
            # Create a backup of the original file
            cp templates/base.html templates/base.html.bak.${TIMESTAMP}
            success_log "Created backup of base.html at templates/base.html.bak.${TIMESTAMP}"
            
            # Remove the swapper link
            sed -i '/<a href="{{ url_for.*pages.swapper.*}}" class="nav-link">Buy Exons<\/a>/d' templates/base.html
            
            success_log "Fixed invalid endpoint reference in base.html"
        else
            success_log "No invalid endpoint references found in base.html"
        fi
    else
        error_log "templates/base.html not found"
    fi
}

# Function to check and fix nginx configuration
check_and_fix_nginx() {
    info_log "Checking nginx configuration for port settings..."
    
    if [ -f "/etc/nginx/sites-available/terminusa.conf" ]; then
        # Create a backup of the original file
        cp /etc/nginx/sites-available/terminusa.conf /etc/nginx/sites-available/terminusa.conf.bak.${TIMESTAMP}
        success_log "Created backup of nginx config at /etc/nginx/sites-available/terminusa.conf.bak.${TIMESTAMP}"
        
        # Check if nginx is configured to proxy to port 5000 instead of 3000 for the main website
        if grep -q "location @proxy_to_app {" /etc/nginx/sites-available/terminusa.conf && grep -q "proxy_pass http://localhost:5000;" /etc/nginx/sites-available/terminusa.conf; then
            info_log "Nginx is configured to proxy main website to port 5000, but web_app.py runs on port ${WEBAPP_PORT}. Fixing..."
            
            # Update the port in the nginx configuration for the main website
            sed -i "s/proxy_pass http:\/\/localhost:5000;/proxy_pass http:\/\/localhost:${WEBAPP_PORT};/g" /etc/nginx/sites-available/terminusa.conf
            
            success_log "Updated main website proxy configuration in nginx"
        fi
        
        # Check if socket.io configuration exists and needs updating
        if grep -q "proxy_pass http://localhost:5000/socket.io;" /etc/nginx/sites-available/terminusa.conf; then
            info_log "Updating socket.io proxy configuration in nginx..."
            
            # Update the port for socket.io
            sed -i "s/proxy_pass http:\/\/localhost:5000\/socket.io;/proxy_pass http:\/\/localhost:${WEBAPP_PORT}\/socket.io;/g" /etc/nginx/sites-available/terminusa.conf
            
            success_log "Updated socket.io proxy configuration in nginx"
        fi
        
        # Keep API endpoints pointing to port 5000
        info_log "Ensuring API endpoints still point to port ${API_PORT}..."
        
        # Test and reload nginx
        if nginx -t; then
            systemctl reload nginx
            success_log "Nginx configuration updated and service reloaded"
        else
            error_log "Nginx configuration test failed. Please check the configuration manually."
        fi
    else
        error_log "Nginx configuration file not found at /etc/nginx/sites-available/terminusa.conf"
    fi
}

# Function to check database connection
check_database_connection() {
    info_log "Checking database connection..."
    if PGPASSWORD=${POSTGRES_PASSWORD} psql -h localhost -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT 1" >/dev/null 2>&1; then
        success_log "Database connection successful"
        return 0
    else
        error_log "Could not connect to database. Please check your database configuration."
        return 1
    fi
}

# Function to check if a port is in use
check_port() {
    local port=$1
    netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "
    return $?
}

# Function to kill process on a port
kill_port_process() {
    local port=$1
    local pid=$(lsof -t -i:$port 2>/dev/null || ss -tlnp 2>/dev/null | grep ":$port " | awk '{print $6}' | cut -d',' -f2 | cut -d'=' -f2)
    if [ ! -z "$pid" ]; then
        kill -9 $pid 2>/dev/null || true
    fi
}

# Screen management functions
check_screen() {
    if ! command_exists screen; then
        info_log "Screen is not installed"
        if [ "$EUID" -eq 0 ]; then
            info_log "Installing screen..."
            apt-get update && apt-get install -y screen
        else
            error_log "Screen is not installed and script is not running with sudo. Please install screen manually."
            return 1
        fi
    fi
    return 0
}

start_screen() {
    local name=$1
    local command=$2
    if ! screen -list | grep -q "$name"; then
        screen -dmS $name bash -c "$command" || {
            error_log "Failed to start screen session: $name"
            return 1
        }
        success_log "Started screen session: $name"
    else
        info_log "Screen session already exists: $name"
    fi
    return 0
}

check_screen_session() {
    local name=$1
    screen -list 2>/dev/null | grep -q "$name"
    return $?
}

kill_screen() {
    local name=$1
    if check_screen_session "$name"; then
        screen -X -S $name quit >/dev/null 2>&1
        success_log "Killed screen session: $name"
    else
        debug_log "Screen session not found: $name"
    fi
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
    
    # Stop system services if running with sudo
    if [ "$EUID" -eq 0 ]; then
        info_log "Stopping system services..."
        systemctl is-active --quiet nginx && systemctl stop nginx
        systemctl is-active --quiet redis-server && systemctl stop redis-server
        systemctl is-active --quiet postgresql && systemctl stop postgresql
        systemctl is-active --quiet postfix && systemctl stop postfix
    else
        info_log "Not running as root, skipping system service management"
    fi
    
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

# Start services
start_services() {
    info_log "Starting services..."
    
    # Check if screen is installed
    check_screen || return 1
    
    # Create logs directory
    mkdir -p logs
    
    # Check and fix configuration issues
    check_and_fix_webapp
    check_and_fix_base_html
    
    # Start system services if running with sudo
    if [ "$EUID" -eq 0 ]; then
        info_log "Starting system services..."
        systemctl start postgresql || error_log "Failed to start PostgreSQL"
        systemctl start redis-server || error_log "Failed to start Redis"
        
        # Fix nginx configuration before starting
        check_and_fix_nginx
        
        systemctl start nginx || error_log "Failed to start Nginx"
        systemctl start postfix || error_log "Failed to start Postfix"
    else
        info_log "Not running as root, skipping system service management"
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        info_log "Virtual environment not found, creating..."
        python3 -m venv venv || {
            error_log "Failed to create virtual environment"
            return 1
        }
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt || {
            error_log "Failed to install dependencies"
            return 1
        }
    else
        # Activate virtual environment
        source venv/bin/activate
    fi
    
    # Start application services in screen sessions
    for service in "${!SERVICE_SCREENS[@]}"; do
        screen_name=${SERVICE_SCREENS[$service]}
        if ! screen -list | grep -q "$screen_name"; then
            case $service in
                "flask")
                    start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python app.py > logs/flask.log 2>&1"
                    ;;
                "webapp")
                    # Check if web_app_simple.py exists and use it instead if available
                    if [ -f "web_app_simple.py" ]; then
                        info_log "Using web_app_simple.py instead of web_app.py"
                        start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python web_app_simple.py > logs/web.log 2>&1"
                    else
                        start_screen "$screen_name" "cd $(pwd) && source venv/bin/activate && python web_app.py > logs/web.log 2>&1"
                    fi
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
    info_log "Waiting for services to start..."
    sleep 5
    
    # Check service status
    show_system_status
    
    success_log "All services started"
}

# System status monitoring
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
        if systemctl is-active --quiet $service 2>/dev/null; then
            printf "%-20s ${GREEN}%-10s${NC} %-20s\n" "$service" "Running" "${SERVICE_PORTS[$service]}"
        else
            printf "%-20s ${RED}%-10s${NC} %-20s\n" "$service" "Stopped" "-"
        fi
    done
    
    # Check screen services
    for service in "${!SERVICE_SCREENS[@]}"; do
        screen_name=${SERVICE_SCREENS[$service]}
        if screen -list 2>/dev/null | grep -q "$screen_name"; then
            printf "%-20s ${GREEN}%-10s${NC} %-20s\n" "$service" "Running" "${SERVICE_PORTS[$service]:-"-"}"
        else
            printf "%-20s ${RED}%-10s${NC} %-20s\n" "$service" "Stopped" "-"
        fi
    done
    
    echo
    echo -e "${YELLOW}Screen Sessions:${NC}"
    screen -list 2>/dev/null | grep -v "There are screens" || echo "No active screens"
    
    # Check database connection
    echo
    echo -e "${YELLOW}Database Status:${NC}"
    if PGPASSWORD=${POSTGRES_PASSWORD} psql -h localhost -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT 1" >/dev/null 2>&1; then
        echo -e "Database Connection: ${GREEN}OK${NC}"
    else
        echo -e "Database Connection: ${RED}FAILED${NC}"
    fi
    
    # Check web application
    echo
    echo -e "${YELLOW}Web Application Status:${NC}"
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:${WEBAPP_PORT} 2>/dev/null | grep -q "200"; then
        echo -e "Web Application: ${GREEN}OK${NC}"
    else
        echo -e "Web Application: ${RED}FAILED${NC}"
    fi
    
    # Check API
    echo
    echo -e "${YELLOW}API Status:${NC}"
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:${API_PORT}/health 2>/dev/null | grep -q "200"; then
        echo -e "API: ${GREEN}OK${NC}"
    else
        echo -e "API: ${RED}FAILED${NC}"
    fi
}

# Show logs menu
show_logs_menu() {
    echo -e "\n${YELLOW}Available Logs:${NC}"
    echo "1) Flask App Log"
    echo "2) Web App Log"
    echo "3) Terminal Server Log"
    echo "4) Game Server Log"
    echo "5) Email Monitor Log"
    echo "6) AI Manager Log"
    echo "7) Combat Manager Log"
    echo "8) Economy Systems Log"
    echo "9) Game Mechanics Log"
    echo "10) Nginx Error Log"
    echo "11) Nginx Access Log"
    echo "12) PostgreSQL Log"
    echo "13) Redis Log"
    echo "14) Mail Log"
    echo "15) Deploy Log"
    echo "0) Back to main menu"
    
    read -p "Select log to view: " log_choice
    case $log_choice in
        1) view_log "logs/flask.log" ;;
        2) view_log "logs/web.log" ;;
        3) view_log "logs/terminal.log" ;;
        4) view_log "logs/game.log" ;;
        5) view_log "logs/email_monitor.log" ;;
        6) view_log "logs/ai_manager.log" ;;
        7) view_log "logs/combat_manager.log" ;;
        8) view_log "logs/economy_systems.log" ;;
        9) view_log "logs/game_mechanics.log" ;;
        10) view_log "/var/log/nginx/error.log" ;;
        11) view_log "/var/log/nginx/access.log" ;;
        12) view_log "/var/log/postgresql/postgresql-main.log" ;;
        13) view_log "/var/log/redis/redis-server.log" ;;
        14) view_log "/var/log/mail.log" ;;
        15) view_log "logs/deploy.log" ;;
        0) return ;;
        *) error_log "Invalid option" ;;
    esac
}

# Function to safely view logs
view_log() {
    local log_file=$1
    if [ -f "$log_file" ]; then
        if command_exists less; then
            less "$log_file"
        else
            tail -n 100 "$log_file"
        fi
    else
        error_log "Log file not found: $log_file"
        read -p "Press Enter to continue..."
    fi
}

# Show database menu
show_database_menu() {
    echo -e "\n${YELLOW}Database Operations:${NC}"
    echo "1) Backup Database"
    echo "2) Restore Database"
    echo "3) Run Migrations"
    echo "4) Initialize Database"
    echo "5) Check Database Status"
    echo "0) Back to main menu"
    
    read -p "Select operation: " db_choice
    case $db_choice in
        1) 
            backup_file="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"
            info_log "Creating database backup: $backup_file"
            mkdir -p "${BACKUP_DIR}"
            if check_database_connection; then
                PGPASSWORD=${POSTGRES_PASSWORD} pg_dump -h localhost -U ${POSTGRES_USER} ${POSTGRES_DB} > "$backup_file"
                if [ $? -eq 0 ]; then
                    success_log "Database backed up to $backup_file"
                else
                    error_log "Database backup failed"
                fi
            fi
            ;;
        2)
            # List available backups
            echo -e "\n${YELLOW}Available backups:${NC}"
            ls -1 "${BACKUP_DIR}" | grep -E "backup_[0-9]+_[0-9]+\.sql" | cat -n
            echo "0) Cancel"
            
            read -p "Select backup to restore (or enter full path): " restore_choice
            if [[ "$restore_choice" =~ ^[0-9]+$ ]]; then
                if [ "$restore_choice" -eq 0 ]; then
                    return
                fi
                
                # Get the selected backup file
                restore_file=$(ls -1 "${BACKUP_DIR}" | grep -E "backup_[0-9]+_[0-9]+\.sql" | sed -n "${restore_choice}p")
                if [ -z "$restore_file" ]; then
                    error_log "Invalid selection"
                    read -p "Press Enter to continue..."
                    return
                fi
                restore_file="${BACKUP_DIR}/${restore_file}"
            else
                restore_file="$restore_choice"
            fi
            
            if [ -f "$restore_file" ]; then
                # Create a backup before restore
                backup_before_restore="${BACKUP_DIR}/before_restore_${TIMESTAMP}.sql"
                info_log "Creating safety backup before restore: $backup_before_restore"
                if check_database_connection; then
                    PGPASSWORD=${POSTGRES_PASSWORD} pg_dump -h localhost -U ${POSTGRES_USER} ${POSTGRES_DB} > "$backup_before_restore"
                    
                    info_log "Restoring database from: $restore_file"
                    PGPASSWORD=${POSTGRES_PASSWORD} psql -h localhost -U ${POSTGRES_USER} ${POSTGRES_DB} < "$restore_file"
                    if [ $? -eq 0 ]; then
                        success_log "Database restored from $restore_file"
                    else
                        error_log "Database restore failed"
                    fi
                fi
            else
                error_log "Backup file not found: $restore_file"
            fi
            ;;
        3)
            info_log "Running database migrations"
            if [ ! -d "venv" ]; then
                error_log "Virtual environment not found. Please initialize the system first."
                read -p "Press Enter to continue..."
                return
            fi
            
            source venv/bin/activate
            if command_exists flask; then
                flask db upgrade
                if [ $? -eq 0 ]; then
                    success_log "Database migrations completed"
                else
                    error_log "Database migrations failed"
                fi
            else
                error_log "Flask command not found. Make sure Flask is installed in your virtual environment."
            fi
            ;;
        4)
            info_log "Initializing database"
            if [ ! -d "venv" ]; then
                error_log "Virtual environment not found. Please initialize the system first."
                read -p "Press Enter to continue..."
                return
            fi
            
            # Create a backup before initialization if database exists
            if check_database_connection; then
                backup_before_init="${BACKUP_DIR}/before_init_${TIMESTAMP}.sql"
                info_log "Creating safety backup before initialization: $backup_before_init"
                PGPASSWORD=${POSTGRES_PASSWORD} pg_dump -h localhost -U ${POSTGRES_USER} ${POSTGRES_DB} > "$backup_before_init"
            fi
            
            source venv/bin/activate
            if [ -f "init_db.py" ]; then
                python init_db.py
                if [ $? -eq 0 ]; then
                    success_log "Database initialized successfully"
                else
                    error_log "Database initialization failed"
                fi
            else
                error_log "init_db.py not found"
            fi
            ;;
        5)
            info_log "Checking database status"
            if check_database_connection; then
                # Show database size
                info_log "Database size information:"
                PGPASSWORD=${POSTGRES_PASSWORD} psql -h localhost -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}')) as db_size;"
                
                # Show table count
                info_log "Table count:"
                PGPASSWORD=${POSTGRES_PASSWORD} psql -h localhost -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT count(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';"
            fi
            ;;
        0) return ;;
        *) error_log "Invalid option" ;;
    esac
    
    read -p "Press Enter to continue..."
}

# Deploy to production function
deploy_production() {
    info_log "Preparing to deploy to production server: ${PROD_SERVER}"
    
    # Check if SSH key is set up
    if ! ssh -o BatchMode=yes -o ConnectTimeout=5 ${PROD_USER}@${PROD_SERVER} echo "SSH connection successful" > /dev/null 2>&1; then
        error_log "SSH connection failed. Make sure your SSH key is set up correctly."
        info_log "You can set up SSH key with: ssh-copy-id ${PROD_USER}@${PROD_SERVER}"
        read -p "Press Enter to continue..."
        return 1
    fi
    
    # Create backup
    backup_file="${BACKUP_DIR}/pre_deploy_${TIMESTAMP}.tar.gz"
    info_log "Creating backup before deployment: $backup_file"
    mkdir -p "${BACKUP_DIR}"
    tar -czf "$backup_file" --exclude="venv" --exclude="node_modules" --exclude=".git" .
    
    # Confirm deployment
    echo
    echo -e "${YELLOW}You are about to deploy to production server: ${PROD_SERVER}${NC}"
    echo "This will update the application code on the production server."
    read -p "Are you sure you want to continue? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        info_log "Deployment cancelled"
        return 0
    fi
    
    # Copy files to production server
    info_log "Copying files to production server..."
    rsync -avz --exclude="venv" --exclude="node_modules" --exclude=".git" --exclude="__pycache__" \
        --exclude="*.pyc" --exclude="logs" --exclude="backups" \
        . ${PROD_USER}@${PROD_SERVER}:${MAIN_APP_DIR}/
    
    # Run setup script on production server
    info_log "Running setup script on production server..."
    ssh ${PROD_USER}@${PROD_SERVER} "cd ${MAIN_APP_DIR} && chmod +x setup_static_files.sh && ./setup_static_files.sh"
    
    # Restart services on production server
    info_log "Restarting services on production server..."
    ssh ${PROD_USER}@${PROD_SERVER} "cd ${MAIN_APP_DIR} && chmod +x deploy.sh && ./deploy.sh restart"
    
    success_log "Deployment to production server completed successfully"
    return 0
}

# Initialize system function
initialize_system() {
    info_log "Initializing system..."
    
    # Create necessary directories
    info_log "Creating directories..."
    mkdir -p static/css static/js static/fonts templates logs
    
    if [ "$EUID" -eq 0 ]; then
        # Create terminusa user if it doesn't exist
        if ! id -u terminusa >/dev/null 2>&1; then
            info_log "Creating terminusa user..."
            useradd -m -d /home/terminusa -s /bin/bash terminusa
        fi

        mkdir -p /var/www/terminusa
        mkdir -p /var/log/terminusa
        
        # Set proper ownership and permissions
        chown -R terminusa:terminusa /var/www/terminusa
        chown -R terminusa:terminusa /var/log/terminusa
        chmod -R 755 /var/www/terminusa
        chmod -R 755 /var/log/terminusa
        
        # Install systemd service
        info_log "Installing systemd service..."
        if [ -f services/terminusa-terminal.service ]; then
            cp services/terminusa-terminal.service /etc/systemd/system/
            systemctl daemon-reload
            systemctl enable terminusa-terminal.service
        fi

        # Install nginx configuration and error pages
        info_log "Setting up nginx configuration..."
        if [ -f nginx/terminusa.conf ]; then
            # Copy nginx configuration
            cp nginx/terminusa.conf /etc/nginx/sites-available/
            ln -sf /etc/nginx/sites-available/terminusa.conf /etc/nginx/sites-enabled/
            rm -f /etc/nginx/sites-enabled/default  # Remove default site
            
            # Create error pages directory
            mkdir -p /var/www/terminusa/nginx/error_pages
            
            # Copy error pages
            cp -r nginx/error_pages/* /var/www/terminusa/nginx/error_pages/
            
            # Set proper permissions
            chown -R www-data:www-data /var/www/terminusa/nginx
            chmod -R 755 /var/www/terminusa/nginx
            
            # Test and restart nginx
            nginx -t && systemctl restart nginx
            success_log "Nginx configuration and error pages installed and service restarted"
        else
            error_log "Nginx configuration file not found"
        fi
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        info_log "Creating virtual environment..."
        python3 -m venv venv || {
            error_log "Failed to create virtual environment"
            return 1
        }
        
        # Install dependencies
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    fi

    # Run static files setup
    info_log "Setting up static files..."
    chmod +x setup_static_files.sh
    ./setup_static_files.sh
    
    # Check and fix configuration issues
    check_and_fix_webapp
    check_and_fix_base_html
    if [ "$EUID" -eq 0 ]; then
        check_and_fix_nginx
    fi
    
    # Setup database if connection is available
    if check_database_connection; then
        info_log "Setting up database..."
        source venv/bin/activate
        if [ -f "init_db.py" ]; then
            python init_db.py
        fi
    fi
    
    success_log "System initialization completed"
    return 0
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
        echo "9) Toggle Debug Mode (current: $DEBUG)"
        echo "0) Exit"
        echo
        read -p "Select an option: " choice
        
        case $choice in
            1) initialize_system ;;
            2) start_services ;;
            3) stop_services ;;
            4) stop_services && sleep 2 && start_services ;;
            5) show_system_status ;;
            6) show_logs_menu ;;
            7) show_database_menu ;;
            8) deploy_production ;;
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
