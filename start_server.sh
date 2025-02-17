[Previous content remains the same until the start_service function, which we'll update:]

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
            debug_log "Starting Gunicorn with web_app.py on port $WEBAPP_PORT"
            # Stop any existing gunicorn processes
            pkill -f "gunicorn.*web_app:app" 2>/dev/null
            rm -f logs/gunicorn.pid 2>/dev/null
            sleep 1
            
            mkdir -p logs
            gunicorn -w 4 -b 0.0.0.0:$WEBAPP_PORT web_app:app --daemon \
                --access-logfile logs/gunicorn-access.log \
                --error-logfile logs/gunicorn-error.log \
                --pid logs/gunicorn.pid
            
            sleep 2  # Give it time to start
            
            if check_service gunicorn; then
                success_log "Gunicorn started successfully on port $WEBAPP_PORT"
            else
                error_log "Failed to start Gunicorn" "Check logs/gunicorn-error.log"
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
            nohup python main.py > logs/game-server.log 2>&1 &
            
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

[Rest of the content remains the same]
