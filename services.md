# Terminusa Online Services

## Core Services

### 1. Web Application Server
- **Service**: Flask Web Application (app_final.py)
- **Port**: 5000
- **Purpose**: Serves the main web interface
- **Dependencies**: Python, Flask, Gevent
- **Implementation**: Uses Gevent WSGI Server (no Gunicorn needed)
- **Start Command**: `python app_final.py`
- **Note**: Gevent provides production-grade WSGI server with async support

### 2. Terminal Server
- **Service**: Terminal WebSocket Server (terminal_server.py)
- **Port**: 6789
- **Purpose**: Handles terminal-based game interactions
- **Dependencies**: Python, WebSocket, Gevent
- **Start Command**: `systemctl start terminusa-terminal.service`

### 3. Database
- **Service**: PostgreSQL
- **Port**: 5432
- **Purpose**: Stores all game data and user information
- **Dependencies**: PostgreSQL 12 or later
- **Start Command**: `systemctl start postgresql`

### 4. Web Server
- **Service**: Nginx
- **Port**: 80, 443
- **Purpose**: Reverse proxy, SSL termination, static file serving
- **Dependencies**: Nginx
- **Start Command**: `systemctl start nginx`

### 5. Redis Server
- **Service**: Redis
- **Port**: 6379
- **Purpose**: Session management, caching
- **Dependencies**: Redis Server
- **Start Command**: `systemctl start redis-server`

## Service Architecture

### Web Application Stack
1. Nginx (Front-end reverse proxy)
2. Gevent WSGI Server (Production WSGI server)
3. Flask Application (Web framework)

### Terminal Server Stack
1. Nginx (WebSocket proxy)
2. Gevent WebSocket Server
3. Terminal Application

## Why Gevent Instead of Gunicorn?

1. **Built-in Async Support**: 
   - Gevent provides native async capabilities needed for WebSocket and real-time features
   - Better integration with our WebSocket-based terminal server

2. **Single Process Model**: 
   - Uses Gevent's coroutines for concurrency
   - Eliminates need for multiple worker processes
   - More memory efficient than multiple Gunicorn workers

3. **Simplified Architecture**:
   - No need for additional WSGI server layer
   - Direct integration with Flask application
   - Better control over async operations

4. **Performance Benefits**:
   - Lower memory footprint
   - Reduced context switching
   - Better suited for long-lived connections

## Service Dependencies

### System Requirements
- Ubuntu 20.04 or later
- Python 3.10 or later
- PostgreSQL 12 or later
- Nginx
- Redis
- Supervisor

### Python Dependencies
- Flask
- SQLAlchemy
- Alembic
- psycopg2-binary
- redis
- gevent (for WSGI server and async operations)
- websockets

## Service Management

### Start All Services
```bash
./manage_services.sh start
```

### Stop All Services
```bash
./manage_services.sh stop
```

### Check Service Status
```bash
./manage_services.sh status
```

### View Logs
```bash
tail -f /var/log/terminusa/app.log
tail -f /var/log/terminusa/terminal.log
tail -f /var/log/nginx/terminusa.access.log
tail -f /var/log/nginx/terminusa.error.log
```

## Monitoring Checklist

- [ ] Check all services are running
- [ ] Monitor system resources (CPU, Memory, Disk)
- [ ] Check application logs for errors
- [ ] Monitor database connections and performance
- [ ] Check SSL certificate expiration
- [ ] Monitor Redis memory usage
- [ ] Check nginx access and error logs
- [ ] Monitor Gevent worker status
