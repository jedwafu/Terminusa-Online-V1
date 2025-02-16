# Terminusa Online

A Solo-leveling inspired MMORPG with CLI and web interfaces.

## System Requirements

### Server Requirements
- Ubuntu 20.04 or later
- Python 3.10 or later
- PostgreSQL 12 or later
- Redis 6 or later
- Nginx
- Screen
- Supervisor

### Client Requirements
- Python 3.8 or later
- Terminal with ANSI color support

## Quick Start

### Server Deployment

1. Clone the repository:
```bash
git clone https://github.com/jedwafu/terminusa-online.git
cd terminusa-online
```

2. Run the deployment script:
```bash
# Linux/Unix
chmod +x deploy.sh
./deploy.sh

# Windows
# Not supported - server must be deployed on Linux/Unix
```

3. Start the server:
```bash
./start_server.sh
```

### CLI Client Installation

#### Windows
1. Navigate to the client directory and run the installation script:
```cmd
cd client
install_client.bat
```

2. Run the client:
```cmd
venv-client\Scripts\activate.bat
python client.py
```

#### Linux/Unix
1. Navigate to the client directory and run the installation script:
```bash
cd client
chmod +x install_client.sh
./install_client.sh
```

2. Run the client:
```bash
source venv-client/bin/activate
python client.py
```

## Server Management

### Screen Session Layout

The server runs in a Screen session with the following windows:
1. Main Server (0)
2. Game Manager (1)
3. Email Monitor (2)
4. System Monitor (3)
5. Log Viewer (4)

### Screen Commands
- `Ctrl+a c`: Create new window
- `Ctrl+a n`: Next window
- `Ctrl+a p`: Previous window
- `Ctrl+a d`: Detach from screen
- `Ctrl+a ?`: Help

To reattach to a detached session:
```bash
screen -r terminusa
```

### Server Monitoring

- Main logs: `logs/main.log`
- Game logs: `logs/game.log`
- Email logs: `logs/email.log`
- Supervisor logs: `logs/supervisor.*.log`

### Database Management

- Reset database: `python reset_db.py`
- Run migrations: `flask db upgrade`
- Create migration: `flask db migrate -m "description"`

## Development

### Setup Development Environment

1. Create virtual environment:
```bash
# Linux/Unix
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
# Server (Linux/Unix only)
pip install -r requirements-server.txt

# Client (Both platforms)
cd client
pip install -r requirements-client.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running Tests

```bash
pytest
pytest --cov=. tests/
```

### Code Style

```bash
black .
flake8
mypy .
```

## Project Structure

```
terminusa-online/
├── client/                 # CLI client
│   ├── client.py          # Client main script
│   ├── install_client.bat # Windows installation script
│   ├── install_client.sh  # Unix installation script
│   └── requirements.txt   # Client dependencies
├── game_systems/          # Game mechanics
├── static/                # Static files
├── templates/             # HTML templates
├── tests/                 # Test suite
├── app.py                 # Main application
├── deploy.sh             # Server deployment script
├── requirements-server.txt # Server dependencies
└── start_server.sh       # Server startup script
```

## Architecture

### Components

1. Main Server
   - Flask web application
   - REST API endpoints
   - WebSocket server
   - Authentication

2. Game Manager
   - Game state management
   - Combat system
   - Gate system
   - Economy system

3. Email Monitor
   - Email verification
   - Password reset
   - Notifications

### Database Schema

- Users
- PlayerCharacters
- Items
- Inventory
- Gates
- Guilds
- Parties
- Transactions

## API Documentation

### Authentication

```
POST /api/login
POST /api/register
POST /api/verify-email
POST /api/request-password-reset
```

### Game

```
GET /api/game/profile
GET /api/game/gates
POST /api/game/gates/{id}/enter
GET /api/game/inventory
```

### Admin

```
GET /api/admin/users
POST /api/admin/users/{id}/ban
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
