#!/bin/bash

# Configuration
REPO_URL="https://github.com/jedwafu/Terminusa-Online-V1.git"
INSTALL_DIR="/root/Terminusa"

echo "Starting deployment..."

# Check if directory exists
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Directory does not exist. Cloning repository..."
    git clone $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
else
    echo "Directory exists. Fetching and resetting to match remote..."
    cd $INSTALL_DIR
    git fetch origin
    git reset --hard origin/master
    git clean -fd
fi

# Create/update .env file
echo "Updating environment configuration..."
cat > .env << EOL
# Flask Configuration
FLASK_SECRET_KEY=Charming123
JWT_SECRET_KEY=Charming123

# Database Configuration
DATABASE_URL=postgresql://termini_admin:strongpassword@localhost/termini

# Solana Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# API Configuration
API_URL=http://localhost:5000

# Server Ports
SERVER_PORT=5000
WEBAPP_PORT=5001

# SSL Configuration
SSL_CERT_PATH=/etc/letsencrypt/live/play.terminusa.online/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/play.terminusa.online/privkey.pem

# Debug Mode
FLASK_DEBUG=True
EOL

# Install/update dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python run_migrations.py

# Restart the application using systemd
echo "Restarting application service..."
if systemctl is-active --quiet terminusa; then
    sudo systemctl restart terminusa
else
    echo "Creating systemd service..."
    cat > /etc/systemd/system/terminusa.service << EOL
[Unit]
Description=Terminusa Online Game Server
After=network.target postgresql.service

[Service]
User=root
WorkingDirectory=/root/Terminusa
Environment=FLASK_APP=main.py
ExecStart=/root/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

    sudo systemctl daemon-reload
    sudo systemctl enable terminusa
    sudo systemctl start terminusa
fi

echo "Deployment completed!"
