# Terminusa Online Services List

## Core Services

### 1. Web Services
- Flask Web Application (app_final.py) - Port 5000
- Terminal WebSocket Server (terminal_server.py) - Port 6789
- Nginx Web Server - Ports 80, 443

### 2. Database Services
- PostgreSQL Database - Port 5432
- Redis Cache Server - Port 6379

### 3. Email Services
- Postfix Mail Server - Port 25
- Email Monitor Service (email_monitor.py)

### 4. Game Services
- Game Server (game_server.py) - Port 5001
- AI Manager (ai_manager.py)
- Combat Manager (combat_manager.py)
- Economy Systems (economy_systems.py)
- Game Mechanics (game_mechanics.py)

### 5. Background Services
- Server Manager (server_manager.py)
- Task Scheduler (Supervisor)

## Service Dependencies
- PostgreSQL -> All services
- Redis -> Web services, Game services
- Nginx -> Web services
- Postfix -> Email services
