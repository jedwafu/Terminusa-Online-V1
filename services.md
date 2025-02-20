# Terminusa Online Services

## Core Services

### 1. Web Application Server
- **Service**: Flask Web Application (app_final.py)
- **Port**: 5000
- **Purpose**: Serves the main web interface
- **Dependencies**: Python, Flask
- **Start Command**: `python app_final.py`

### 2. Terminal Server
- **Service**: Terminal WebSocket Server (terminal_server.py)
- **Port**: 6789
- **Purpose**: Handles terminal-based game interactions
- **Dependencies**: Python, WebSocket
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

## Supporting Services

### 6. SSL Certificate Manager
- **Service**: Certbot
- **Purpose**: SSL certificate automation
- **Dependencies**: Certbot
- **Renewal Command**: `certbot renew`

### 7. Task Scheduler
- **Service**: Supervisor
- **Purpose**: Process management and monitoring
- **Dependencies**: Supervisor
- **Start Command**: `systemctl start supervisor`

## Monitoring Services

### 8. Logging Service
- **Service**: System Logging
- **Location**: /var/log/terminusa/
- **Purpose**: Application and error logging
- **Dependencies**: logrotate
- **Log Rotation**: Daily with 7-day retention

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
- gevent
- websockets

## Service Configuration Files

### 1. Nginx Configuration
- Main config: `/etc/nginx/nginx.conf`
- Site config: `/etc/nginx/conf.d/terminusa.conf`
- Terminal config: `/etc/nginx/conf.d/terminusa-terminal.conf`

### 2. Supervisor Configuration
- Terminal service: `/etc/supervisor/conf.d/terminusa-terminal.conf`

### 3. System Service Files
- Terminal service: `/etc/systemd/system/terminusa-terminal.service`

### 4. Environment Configuration
- Main config: `.env`
- Example config: `.env.example`

## Service Management Commands

### Start All Services
```bash
systemctl start postgresql
systemctl start redis-server
systemctl start nginx
systemctl start supervisor
systemctl start terminusa-terminal.service
python app_final.py
```

### Stop All Services
```bash
systemctl stop terminusa-terminal.service
systemctl stop nginx
systemctl stop redis-server
systemctl stop postgresql
systemctl stop supervisor
```

### Check Service Status
```bash
systemctl status postgresql
systemctl status redis-server
systemctl status nginx
systemctl status supervisor
systemctl status terminusa-terminal.service
```

### View Logs
```bash
tail -f /var/log/terminusa/app.log
tail -f /var/log/terminusa/terminal.log
tail -f /var/log/nginx/terminusa.access.log
tail -f /var/log/nginx/terminusa.error.log
```

## Maintenance Tasks

### Database Backup
```bash
pg_dump -U terminusa terminusa_db > backup.sql
```

### SSL Certificate Renewal
```bash
certbot renew
```

### Log Rotation
```bash
logrotate /etc/logrotate.d/terminusa
```

## Monitoring Checklist

- [ ] Check all services are running
- [ ] Monitor system resources (CPU, Memory, Disk)
- [ ] Check application logs for errors
- [ ] Monitor database connections and performance
- [ ] Check SSL certificate expiration
- [ ] Monitor Redis memory usage
- [ ] Check nginx access and error logs
