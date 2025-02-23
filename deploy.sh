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

# Enhanced setup_static_files with better error handling and update functionality
setup_static_files() {
    info_log "Setting up static files..."
    
    # Load environment variables
    if [ -f .env ]; then
        set -a
        source .env
        set +a
    else
        error_log ".env file not found"
        return 1
    fi

    # Define directories
    STATIC_DIR="${STATIC_DIR:-/var/www/terminusa/static}"
    SOURCE_DIR="${SOURCE_DIR:-./static}"
    NGINX_ROOT="/var/www/terminusa"
    NGINX_STATIC_DIR="$STATIC_DIR"
    PROJECT_ROOT=$(pwd)
    BACKUP_DIR="$NGINX_ROOT/static_backup_$(date +%Y%m%d_%H%M%S)"
    
    # Create directories with error handling
    info_log "Creating static directories..."
    sudo mkdir -p "$NGINX_STATIC_DIR/css" || { error_log "Failed to create CSS directory"; return 1; }
    sudo mkdir -p "$NGINX_STATIC_DIR/js" || { error_log "Failed to create JS directory"; return 1; }
    sudo mkdir -p "$NGINX_STATIC_DIR/images" || { error_log "Failed to create images directory"; return 1; }
    
    # Verify source directories exist
    [ -d "$SOURCE_DIR/css" ] || { error_log "Source CSS directory not found"; return 1; }
    [ -d "$SOURCE_DIR/js" ] || { error_log "Source JS directory not found"; return 1; }

    # Backup existing files if they exist
    if [ -d "$NGINX_STATIC_DIR" ]; then
        info_log "Backing up existing static files..."
        sudo cp -r "$NGINX_STATIC_DIR" "$BACKUP_DIR" || { error_log "Failed to create backup"; return 1; }
    fi
    
    # Copy files with error handling
    info_log "Copying static files..."
    
    # Copy CSS files
    info_log "Copying CSS files..."
    sudo cp -r "$SOURCE_DIR/css/"* "$NGINX_STATIC_DIR/css/" || { error_log "Failed to copy CSS files"; return 1; }
    
    # Copy JS files
    info_log "Copying JavaScript files..."
    sudo cp -r "$SOURCE_DIR/js/"* "$NGINX_STATIC_DIR/js/" || { error_log "Failed to copy JS files"; return 1; }
    
    # Copy images
    info_log "Copying image files..."
    sudo cp -r "$SOURCE_DIR/images/"* "$NGINX_STATIC_DIR/images/" 2>/dev/null || info_log "No images found"
    
    # Set permissions
    info_log "Setting permissions..."
    sudo chown -R www-data:www-data "$NGINX_ROOT" || { error_log "Failed to set ownership"; return 1; }
    sudo chmod -R 755 "$NGINX_ROOT" || { error_log "Failed to set permissions"; return 1; }
    sudo find "$NGINX_STATIC_DIR" -type f -exec chmod 644 {} \;
    
    # Verify nginx directory exists
    if [ ! -d "/var/www/terminusa" ]; then
        error_log "Nginx directory /var/www/terminusa not found"
        return 1
    fi

    # Create symbolic link
    ln -sfn "$NGINX_STATIC_DIR" "/var/www/terminusa/static" || { error_log "Failed to create symbolic link"; return 1; }

    # Clear nginx cache and restart
    info_log "Clearing nginx cache and restarting..."
    sudo rm -rf /var/cache/nginx/*
    sudo systemctl restart nginx
    
    # Verify nginx configuration and restart
    info_log "Verifying nginx configuration and restarting..."
    if ! sudo nginx -t; then
        error_log "Nginx configuration test failed!"
        if [ -d "$BACKUP_DIR" ]; then
            info_log "Restoring from backup..."
            sudo rm -rf $NGINX_STATIC_DIR
            sudo cp -r $BACKUP_DIR/* $NGINX_STATIC_DIR/
        fi
        return 1
    fi
    
    # Reload nginx
    info_log "Reloading nginx..."
    sudo systemctl reload nginx
    
    # Verify file access
    info_log "Verifying file access..."
    if ! sudo -u www-data test -r "$NGINX_STATIC_DIR/css/style.css"; then
        error_log "www-data cannot read style.css"
        return 1
    fi
    
    success_log "Static files setup completed successfully"
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

# Enhanced nginx setup with configuration installer
setup_nginx() {
    info_log "Setting up nginx..."

    # Backup existing configuration if it exists
    if [ -f /etc/nginx/sites-available/terminusa.conf ]; then
        backup_file="/etc/nginx/sites-available/terminusa.conf.backup_$(date +%Y%m%d_%H%M%S)"
        info_log "Backing up existing nginx config to $backup_file"
        sudo cp /etc/nginx/sites-available/terminusa.conf "$backup_file"
    fi

    # Update nginx user
    sudo sed -i 's/user root/user www-data/' /etc/nginx/nginx.conf

    # Create nginx configuration
    info_log "Creating nginx configuration..."
    sudo tee /etc/nginx/sites-available/terminusa.conf > /dev/null << 'EOL'
server {
    listen 80;
    server_name terminusa.online;

    # SSL configuration
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/terminusa.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/terminusa.online/privkey.pem;

    # Root directory
    root /var/www/terminusa;

    # Static files
    location /static/ {
        alias /var/www/terminusa/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
        
        # Enable gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 10240;
        gzip_proxied expired no-cache no-store private auth;
        gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml;
        gzip_disable "MSIE [1-6]\.";
        
        # Proper MIME type handling
        include /etc/nginx/mime.types;
        default_type application/octet-stream;
        
        # Specific MIME types for web files
        types {
            text/css css;
            text/javascript js;
            image/svg+xml svg svgz;
            image/png png;
            image/jpeg jpg jpeg;
            image/gif gif;
            image/x-icon ico;
            font/woff woff;
            font/woff2 woff2;
            application/font-woff woff;
            application/font-woff2 woff2;
        }
        
        # Try to serve the exact file, then directory index, then 404
        try_files \$uri \$uri/ =404;
        
        # Add CORS headers
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
        
        # Cache settings
        add_header Cache-Control "public, max-age=2592000";
        etag on;
        
        # Security headers
        add_header X-Content-Type-Options "nosniff";
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-XSS-Protection "1; mode=block";
    }

    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }

    # Additional security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Client caching for common file types
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg)\$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
        
        # Ensure CSS files are served with correct MIME type
        location ~* \.css$ {
            add_header Content-Type text/css;
            add_header X-Content-Type-Options nosniff;
        }
        
        # Ensure JS files are served with correct MIME type
        location ~* \.js$ {
            add_header Content-Type application/javascript;
            add_header X-Content-Type-Options nosniff;
        }
    }
}
EOL

    # Enable site
    info_log "Enabling nginx site..."
    sudo ln -sf /etc/nginx/sites-available/terminusa.conf /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default

    # Test configuration
    info_log "Testing nginx configuration..."
    if ! sudo nginx -t; then
        error_log "Nginx configuration test failed!"
        if [ -f "$backup_file" ]; then
            info_log "Restoring backup configuration..."
            sudo cp "$backup_file" /etc/nginx/sites-available/terminusa.conf
            sudo nginx -t && sudo systemctl restart nginx
        fi
        return 1
    fi

    # Restart nginx
    info_log "Restarting nginx..."
    if ! sudo systemctl restart nginx; then
        error_log "Failed to restart nginx!"
        if [ -f "$backup_file" ]; then
            info_log "Restoring backup configuration..."
            sudo cp "$backup_file" /etc/nginx/sites-available/terminusa.conf
            sudo nginx -t && sudo systemctl restart nginx
        fi
        return 1
    fi

    # Verify nginx is running
    if ! systemctl is-active --quiet nginx; then
        error_log "Nginx is not running after configuration update!"
        if [ -f "$backup_file" ]; then
            info_log "Restoring backup configuration..."
            sudo cp "$backup_file" /etc/nginx/sites-available/terminusa.conf
            sudo nginx -t && sudo systemctl restart nginx
        fi
        return 1
    fi

    success_log "Nginx setup completed successfully"
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
    
    # Test SSH connection
    info_log "Testing SSH connection..."
    if ! ssh -q $PROD_USER@$PROD_SERVER exit; then
        error_log "SSH connection failed. Please check your SSH key setup."
        return 1
    fi
    
    # Create backups
    info_log "Creating backups..."
    if ! ssh $PROD_USER@$PROD_SERVER "mkdir -p $BACKUP_DIR"; then
        error_log "Failed to create backup directory"
        return 1
    fi
    
    if ! ssh $PROD_USER@$PROD_SERVER "
        if [ -d $MAIN_APP_DIR ]; then 
            tar -czf $BACKUP_DIR/terminusa-web_$TIMESTAMP.tar.gz -C $MAIN_APP_DIR .;
        fi;
        if [ -d $GAME_APP_DIR ]; then 
            tar -czf $BACKUP_DIR/terminusa-game_$TIMESTAMP.tar.gz -C $GAME_APP_DIR .;
        fi
    "; then
        error_log "Failed to create backups"
        return 1
    fi
    
    # Create deployment packages
    info_log "Creating deployment packages..."
    
    # Create deployment package
    info_log "Creating deployment package..."
    if [ "$DEBUG" = true ]; then
        debug_log "Current directory: $(pwd)"
        debug_log "Directory contents: $(ls -la)"
    fi
    
    tar -czvf deploy.tar.gz \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='.env' \
        --exclude='node_modules' \
        --exclude='tests' \
        --exclude='*.log' \
        --exclude='pytest.ini' \
        . || {
            error_log "Failed to create deployment package"
            return 1
        }
    
    if [ ! -f deploy.tar.gz ]; then
        error_log "Deployment package was not created"
        return 1
    fi
    
    info_log "Deployment package created successfully"
    
    # Upload and deploy
    info_log "Uploading deployment package..."
    if ! scp deploy.tar.gz $PROD_USER@$PROD_SERVER:/tmp/; then
        error_log "Failed to upload deployment package"
        return 1
    fi
    
    info_log "Deploying to main website directory..."
    if ! ssh $PROD_USER@$PROD_SERVER "
        set -e
        systemctl stop terminusa-web || true
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
    "; then
        error_log "Failed to deploy main website"
        return 1
    fi
    success_log "Main website deployed successfully"
    
    info_log "Deploying to game application directory..."
    if ! ssh $PROD_USER@$PROD_SERVER "
        set -e
        systemctl stop terminusa-game terminusa-terminal || true
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
        rm -f /tmp/deploy.tar.gz
    "; then
        error_log "Failed to deploy game application"
        return 1
    fi
    success_log "Game application deployed successfully"
    
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
