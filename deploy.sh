#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Terminusa Online Deployment${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    nginx \
    supervisor \
    redis-server \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    screen \
    htop

# Create and activate virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements-server.txt

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p static/uploads

# Initialize PostgreSQL database
echo -e "${YELLOW}Setting up PostgreSQL...${NC}"
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw terminusa; then
    sudo -u postgres createdb terminusa
    sudo -u postgres createuser terminusa_user
    sudo -u postgres psql -c "ALTER USER terminusa_user WITH PASSWORD 'strongpassword';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE terminusa TO terminusa_user;"
fi

# Initialize Redis
echo -e "${YELLOW}Setting up Redis...${NC}"
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Initialize the database
echo -e "${YELLOW}Initializing application database...${NC}"
python reset_db.py

# Set up environment variables if .env doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    # Generate new secret keys
    sed -i "s/your-secret-key-here/$(python3 -c 'import secrets; print(secrets.token_hex(32))')/" .env
    sed -i "s/your-jwt-secret-key-here/$(python3 -c 'import secrets; print(secrets.token_hex(32))')/" .env
    sed -i "s/your-password-salt-here/$(python3 -c 'import secrets; print(secrets.token_hex(16))')/" .env
fi

# Set up Nginx if it's not already configured
if [ ! -f /etc/nginx/sites-available/terminusa ]; then
    echo -e "${YELLOW}Setting up Nginx configuration...${NC}"
    sudo bash -c 'cat > /etc/nginx/sites-available/terminusa << EOL
server {
    listen 80;
    server_name terminusa.online www.terminusa.online;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name terminusa.online www.terminusa.online;

    ssl_certificate /etc/letsencrypt/live/terminusa.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/terminusa.online/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://localhost:5000/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }

    location /static {
        alias /root/Terminusa/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}

server {
    listen 80;
    server_name play.terminusa.online;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name play.terminusa.online;

    ssl_certificate /etc/letsencrypt/live/play.terminusa.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/play.terminusa.online/privkey.pem;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://localhost:5001/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }

    location /static {
        alias /root/Terminusa/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
EOL'

    sudo ln -s /etc/nginx/sites-available/terminusa /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl restart nginx
fi

# Set up Supervisor configuration
echo -e "${YELLOW}Setting up Supervisor configuration...${NC}"
sudo bash -c 'cat > /etc/supervisor/conf.d/terminusa.conf << EOL
[program:terminusa]
directory=/root/Terminusa
command=/root/Terminusa/venv/bin/gunicorn -w 4 -k gevent -b 127.0.0.1:5000 main:app
autostart=true
autorestart=true
stderr_logfile=/root/Terminusa/logs/supervisor.err.log
stdout_logfile=/root/Terminusa/logs/supervisor.out.log
environment=PYTHONPATH="/root/Terminusa"

[program:terminusa_play]
directory=/root/Terminusa
command=/root/Terminusa/venv/bin/gunicorn -w 4 -k gevent -b 127.0.0.1:5001 play:app
autostart=true
autorestart=true
stderr_logfile=/root/Terminusa/logs/supervisor_play.err.log
stdout_logfile=/root/Terminusa/logs/supervisor_play.out.log
environment=PYTHONPATH="/root/Terminusa"
EOL'

sudo supervisorctl reread
sudo supervisorctl update

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Run ./start_server.sh to start the server${NC}"

# Make start_server.sh executable
chmod +x start_server.sh
