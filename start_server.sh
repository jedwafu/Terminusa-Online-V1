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
declare -A SERVICE_REQUIRED

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Get webapp port from environment or use default
WEBAPP_PORT=${WEBAPP_PORT:-5001}

# Initialize arrays
SERVICE_PORTS=(
    ["postgresql"]="5432"
    ["nginx"]="80"
    ["gunicorn"]="$WEBAPP_PORT"
    ["game-server"]="5000"
    ["postfix"]="25"
)

SERVICE_LOGS=(
    ["postgresql"]="/var/log/postgresql/postgresql-main.log"
    ["nginx"]="/var/log/nginx/error.log"
    ["gunicorn"]="logs/gunicorn.log"
    ["game-server"]="logs/game-server.log"
    ["postfix"]="/var/log/mail.log"
)

# Mark required services
SERVICE_REQUIRED=(
    ["postgresql"]="true"
    ["nginx"]="true"
    ["gunicorn"]="true"
    ["game-server"]="true"
    ["postfix"]="true"
)

# Optional services - will be added only if installed
OPTIONAL_SERVICES=(
    "redis"
    "elasticsearch"
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
    if [ "$DEBUG" = true ] && [ ! -z "$2" ]; then
        echo -e "${RED}[ERROR DETAILS] $2${NC}"
    fi
    # Log to file instead of using logger command
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/server.log
}

# Success logging function
success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    # Log to file instead of using logger command
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/server.log
}

# Info logging function
info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    # Log to file instead of using logger command
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/server.log
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

# Check if a service is installed
check_service_installed() {
    local service=$1
    case $service in
        "postgresql")
            command -v psql >/dev/null 2>&1
            return $?
            ;;
        "nginx")
            command -v nginx >/dev/null 2>&1
            return $?
            ;;
        "redis")
            command -v redis-server >/dev/null 2>&1
            return $?
            ;;
        "elasticsearch")
            systemctl list-unit-files | grep -q elasticsearch.service
            return $?
            ;;
        "postfix")
            command -v postfix >/dev/null 2>&1
            return $?
            ;;
        *)
            return 0  # Assume Python services are always available
            ;;
    esac
}

# Check if port is in use and kill the process
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

# Check service status
check_service() {
    local service=$1
    local port=${SERVICE_PORTS[$service]}
    
    case $service in
        "postgresql")
            if pg_isready >/dev/null 2>&1; then
                SERVICE_STATUS[$service]="running"
                SERVICE_PIDS[$service]=$(pgrep -x postgres | head -n1)
                debug_log "$service is running with PID ${SERVICE_PIDS[$service]}"
                return 0
            else
                SERVICE_STATUS[$service]="stopped"
                debug_log "$service is stopped"
                return 1
            fi
            ;;
        "nginx")
            if pgrep -x nginx >/dev/null; then
                SERVICE_STATUS[$service]="running"
                SERVICE_PIDS[$service]=$(pgrep -x nginx | head -n1)
                debug_log "$service is running with PID ${SERVICE_PIDS[$service]}"
                return 0
            else
                SERVICE_STATUS[$service]="stopped"
                debug_log "$service is stopped"
                return 1
            fi
            ;;
        "gunicorn")
            local pid=$(pgrep -f "gunicorn.*app_final:app" | head -n1)
            if [ ! -z "$pid" ] && ss -tuln | grep -q ":$WEBAPP_PORT "; then
                SERVICE_STATUS[$service]="running"
                SERVICE_PIDS[$service]=$pid
                debug_log "$service is running with PID $pid on port $WEBAPP_PORT"
                return 0
            else
                SERVICE_STATUS[$service]="stopped"
                debug_log "$service is stopped"
                return 1
            fi
            ;;
        "game-server")
            local pid=$(pgrep -f "python.*main.py" | head -n1)
            if [ ! -z "$pid" ] && ss -tuln | grep -q ":5000 "; then
                SERVICE_STATUS[$service]="running"
                SERVICE_PIDS[$service]=$pid
                debug_log "$service is running with PID $pid"
                return 0
            else
                SERVICE_STATUS[$service]="stopped"
                debug_log "$service is stopped"
                return 1
            fi
            ;;
        "postfix")
            if pgrep -x master >/dev/null; then
                SERVICE_STATUS[$service]="running"
                SERVICE_PIDS[$service]=$(pgrep -x master | head -n1)
                debug_log "$service is running with PID ${SERVICE_PIDS[$service]}"
                return 0
            else
                SERVICE_STATUS[$service]="stopped"
                debug_log "$service is stopped"
                return 1
            fi
            ;;
        "redis")
            if pgrep -x redis-server >/dev/null; then
                SERVICE_STATUS[$service]="running"
                SERVICE_PIDS[$service]=$(pgrep -x redis-server | head -n1)
                debug_log "$service is running with PID ${SERVICE_PIDS[$service]}"
                return 0
            else
                SERVICE_STATUS[$service]="stopped"
                debug_log "$service is stopped"
                return 1
            fi
            ;;
        *)
            error_log "Unknown service: $service"
            return 1
            ;;
    esac
}

# Start a specific service
start_service() {
    local service=$1
    info_log "Starting $service..."
    
    # Get service port
    local port=${SERVICE_PORTS[$service]}
    
    # Stop any existing process using the port
    if [ ! -z "$port" ]; then
        kill_port_process $port
    fi
    
    case $service in
        "postgresql")
            systemctl stop postgresql 2>/dev/null
            sleep 1
            systemctl start postgresql
            if check_service postgresql; then
                success_log "PostgreSQL started successfully"
            else
                error_log "Failed to start PostgreSQL" "$(systemctl status postgresql)"
                return 1
            fi
            ;;
        "nginx")
            systemctl stop nginx 2>/dev/null
            sleep 1
            # Verify nginx configuration
            nginx -t
            if [ $? -ne 0 ]; then
                error_log "Nginx configuration test failed"
                return 1
            fi
            
            systemctl start nginx
            if check_service nginx; then
                success_log "Nginx started successfully"
            else
                error_log "Failed to start Nginx" "$(systemctl status nginx)"
                return 1
            fi
            ;;
        "gunicorn")
            debug_log "Starting Gunicorn with app_final.py on port $WEBAPP_PORT"
            # Stop any existing gunicorn processes
            pkill -f "gunicorn.*app_final:app" 2>/dev/null
            rm -f logs/gunicorn.pid 2>/dev/null
            sleep 1
            
            mkdir -p logs
            
            # Activate virtual environment if it exists
            if [ -f "venv/bin/activate" ]; then
                source venv/bin/activate
            fi
            
            # Start Gunicorn with gevent worker
            gunicorn "app_final:app" \
                --bind "0.0.0.0:$WEBAPP_PORT" \
                --worker-class "gevent" \
                --workers "1" \
                --timeout "120" \
                --daemon \
                --capture-output \
                --access-logfile "logs/gunicorn-access.log" \
                --error-logfile "logs/gunicorn-error.log" \
                --pid "logs/gunicorn.pid" \
                --log-level "debug" \
                --reload
            
            sleep 2  # Give it time to start
            
            if check_service gunicorn; then
                success_log "Gunicorn started successfully on port $WEBAPP_PORT"
            else
                error_log "Failed to start Gunicorn" "$(tail -n 10 logs/gunicorn-error.log)"
                return 1
            fi
            ;;
        "game-server")
            debug_log "Starting game server with main.py"
            # Stop any existing game server processes
            pkill -f "python.*main.py" 2>/dev/null
            sleep 1
            
            mkdir -p logs
            # Clear the log file
            > logs/game-server.log
            
            # Start with proper environment
            source venv/bin/activate
            export PYTHONPATH=$PWD
            python main.py > logs/game-server.log 2>&1 &
            echo $! > logs/game-server.pid
            
            sleep 2  # Give it time to start
            
            if check_service game-server; then
                success_log "Game server started successfully"
            else
                error_log "Failed to start game server" "Check logs/game-server.log"
                tail -n 10 logs/game-server.log
                return 1
            fi
            ;;
        "postfix")
            systemctl stop postfix 2>/dev/null
            sleep 1
            systemctl start postfix
            if check_service postfix; then
                success_log "Postfix started successfully"
            else
                error_log "Failed to start Postfix" "$(systemctl status postfix)"
                return 1
            fi
            ;;
        "redis")
            systemctl stop redis-server 2>/dev/null
            sleep 1
            systemctl start redis-server
            if check_service redis; then
                success_log "Redis started successfully"
            else
                error_log "Failed to start Redis" "$(systemctl status redis-server)"
                return 1
            fi
            ;;
        *)
            error_log "Unknown service: $service"
            return 1
            ;;
    esac
}

# Stop a specific service
stop_service() {
    local service=$1
    info_log "Stopping $service..."
    
    case $service in
        "postgresql"|"nginx"|"postfix"|"redis")
            systemctl stop $service
            if ! check_service $service; then
                success_log "$service stopped successfully"
            else
                error_log "Failed to stop $service" "$(systemctl status $service)"
                return 1
            fi
            ;;
        "gunicorn")
            if [ -f logs/gunicorn.pid ]; then
                kill -TERM $(cat logs/gunicorn.pid)
                rm -f logs/gunicorn.pid
            else
                pkill -f "gunicorn.*web_app:app"
            fi
            
            if ! check_service gunicorn; then
                success_log "Gunicorn stopped successfully"
            else
                error_log "Failed to stop Gunicorn"
                return 1
            fi
            ;;
        "game-server")
            # Try graceful shutdown first
            pkill -TERM -f "python.*main.py"
            sleep 2
            
            # Force kill all related processes
            pkill -9 -f "python.*main.py" 2>/dev/null
            pkill -9 -f "python.*game_server" 2>/dev/null
            pkill -9 -f "python.*server_manager" 2>/dev/null
            sleep 1
            
            # Kill any process using game server port
            local port=${SERVICE_PORTS[$service]}
            if [ ! -z "$port" ]; then
                fuser -k -n tcp $port 2>/dev/null
                local pid=$(lsof -t -i:$port 2>/dev/null)
                if [ ! -z "$pid" ]; then
                    kill -9 $pid 2>/dev/null
                fi
            fi
            
            # Final check and cleanup
            if pgrep -f "python.*main.py|python.*game_server|python.*server_manager" > /dev/null; then
                pkill -9 -f "python.*main.py|python.*game_server|python.*server_manager"
                sleep 1
            fi
            
            if ! check_service game-server; then
                success_log "Game server stopped successfully"
            else
                error_log "Failed to stop game server"
                # Continue anyway since we've done everything possible to stop it
                return 0
            fi
            ;;
        *)
            error_log "Unknown service: $service"
            return 1
            ;;
    esac
}

# Show service status
show_status() {
    info_log "Checking service status..."
    printf "${YELLOW}%-20s %-10s %-20s${NC}\n" "Service" "Status" "Details"
    echo "----------------------------------------------------"
    
    for service in "${!SERVICE_PORTS[@]}"; do
        check_service $service
        local status=${SERVICE_STATUS[$service]}
        local pid=${SERVICE_PIDS[$service]}
        local port=${SERVICE_PORTS[$service]}
        
        if [ "$status" = "running" ]; then
            local details="PID: $pid, Port: $port"
            printf "%-20s ${GREEN}%-10s${NC} %-20s\n" "$service" "$status" "$details"
        else
            printf "%-20s ${RED}%-10s${NC} %-20s\n" "$service" "$status" "Not running"
        fi
    done
}

# Monitor services function
monitor_services() {
    local header_printed=false
    
    while [ "$MONITOR_RUNNING" = true ]; do
        clear
        echo -e "${CYAN}=== Terminusa Online Service Monitor ===${NC}"
        echo -e "Time: $(date '+%Y-%m-%d %H:%M:%S')\n"
        
        # Print header
        printf "%-15s %-10s %-10s %-10s %-10s %-10s %-20s\n" \
            "Service" "Status" "PID" "CPU%" "MEM%" "Port" "Connections"
        echo "--------------------------------------------------------------------------------"
        
        # Check each service
        for service in "${!SERVICE_PORTS[@]}"; do
            check_service $service
            local status=${SERVICE_STATUS[$service]}
            local pid=${SERVICE_PIDS[$service]}
            local port=${SERVICE_PORTS[$service]}
            local connections=0
            
            # Get resource usage
            read cpu mem vsz <<< $(get_service_resources "$service")
            
            # Count connections if service is running
            if [ "$status" = "running" ] && [ ! -z "$port" ]; then
                connections=$(netstat -an | grep ":$port " | grep ESTABLISHED | wc -l)
            fi
            
            # Print service status
            if [ "$status" = "running" ]; then
                printf "%-15s ${GREEN}%-10s${NC} %-10s %-10.1f %-10.1f %-10s %-20s\n" \
                    "$service" "RUNNING" "$pid" "$cpu" "$mem" "$port" "$connections"
            else
                printf "%-15s ${RED}%-10s${NC} %-10s %-10.1f %-10.1f %-10s %-20s\n" \
                    "$service" "STOPPED" "-" "0.0" "0.0" "$port" "0"
            fi
        done
        
        echo -e "\n${CYAN}=== System Resources ===${NC}"
        echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
        echo "Memory Usage: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')"
        echo "Disk Usage: $(df -h / | awk 'NR==2{print $5}')"
        
        sleep $MONITOR_INTERVAL
    done
}

# Initialize services
initialize_services() {
    info_log "Initializing services..."
    
    # Create required directories
    mkdir -p logs
    mkdir -p instance
    mkdir -p static/downloads
    
    # Set proper permissions
    chmod -R 755 static
    chmod +x *.py
    
    # Configure Nginx
    if [ ! -f "/etc/nginx/sites-available/terminusa" ]; then
        info_log "Configuring Nginx..."
        cat > /etc/nginx/sites-available/terminusa << EOL
server {
    listen 80;
    server_name play.terminusa.online;

    location / {
        proxy_pass http://127.0.0.1:$WEBAPP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /root/Terminusa/static;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:$WEBAPP_PORT/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOL
        ln -sf /etc/nginx/sites-available/terminusa /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
    fi
    
    return 0
}

# Show help message
show_help() {
    echo -e "${YELLOW}Terminusa Online Server Management${NC}"
    echo
    echo "Usage: $0 [options] [service]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -d, --debug    Enable debug output"
    echo "  start          Start all services or specific service"
    echo "  stop           Stop all services or specific service"
    echo "  restart        Restart all services or specific service"
    echo "  status         Show service status"
    echo "  monitor        Show real-time service monitoring"
    echo
    echo "Services:"
    echo "  postgresql     Database server"
    echo "  nginx         Web server"
    echo "  gunicorn      Application server (port $WEBAPP_PORT)"
    echo "  game-server   Game server (port 5000)"
    echo "  postfix       Mail server"
    echo "  redis         Cache server (optional)"
    echo "  all           All services"
    echo
    echo "Examples:"
    echo "  $0 start                # Start all services"
    echo "  $0 start postgresql     # Start only PostgreSQL"
    echo "  $0 stop nginx          # Stop only Nginx"
    echo "  $0 status              # Show all service status"
    echo "  $0 -d start           # Start all services with debug output"
    echo "  $0 monitor            # Show real-time monitoring"
}

# Cleanup function
cleanup() {
    MONITOR_RUNNING=false
    info_log "Cleaning up..."
    stop_service game-server
    stop_service gunicorn
    stop_service nginx
    stop_service postfix
    stop_service postgresql
    success_log "Cleanup complete"
}

# Main script execution
main() {
    # Process command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--debug)
                DEBUG=true
                shift
                ;;
            start|stop|restart|status|monitor)
                ACTION=$1
                shift
                ;;
            postgresql|nginx|gunicorn|game-server|postfix|redis|all)
                SERVICE=$1
                if [ "$SERVICE" != "all" ] && ! check_service_installed "$SERVICE"; then
                    error_log "Service $SERVICE is not installed"
                    exit 1
                fi
                shift
                ;;
            *)
                error_log "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Create logs directory if it doesn't exist
    mkdir -p logs

    # Set up trap for cleanup
    trap cleanup SIGINT SIGTERM

    # Initialize if needed
    if [ "$ACTION" = "start" ]; then
        initialize_services || exit 1
    fi

    # Process the action
    case $ACTION in
        start)
            if [ "$SERVICE" = "all" ] || [ -z "$SERVICE" ]; then
                info_log "Starting all services..."
                start_service postgresql
                start_service nginx
                start_service postfix
                start_service gunicorn
                start_service game-server
            else
                start_service $SERVICE
            fi
            ;;
        stop)
            if [ "$SERVICE" = "all" ] || [ -z "$SERVICE" ]; then
                info_log "Stopping all services..."
                stop_service game-server
                stop_service gunicorn
                stop_service nginx
                stop_service postfix
                stop_service postgresql
            else
                stop_service $SERVICE
            fi
            ;;
        restart)
            if [ "$SERVICE" = "all" ] || [ -z "$SERVICE" ]; then
                info_log "Restarting all services..."
                stop_service game-server
                stop_service gunicorn
                stop_service nginx
                stop_service postfix
                stop_service postgresql
                sleep 2
                start_service postgresql
                start_service postfix
                start_service nginx
                start_service gunicorn
                start_service game-server
            else
                stop_service $SERVICE
                sleep 2
                start_service $SERVICE
            fi
            ;;
        status)
            show_status
            ;;
        monitor)
            monitor_services
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"
