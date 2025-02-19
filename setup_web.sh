#!/bin/bash

# Stop on any error
set -e

echo "Setting up web server and static files..."

# Create web directories
WEB_ROOT="/var/www/terminusa"
STATIC_DIR="$WEB_ROOT/static"

echo "Creating directories..."
sudo mkdir -p $WEB_ROOT
sudo mkdir -p $STATIC_DIR/css
sudo mkdir -p $STATIC_DIR/js
sudo mkdir -p $STATIC_DIR/images

# Copy static files
echo "Copying static files..."
sudo cp -r static/css/* $STATIC_DIR/css/
sudo cp -r static/js/* $STATIC_DIR/js/
sudo cp -r static/images/* $STATIC_DIR/images/ 2>/dev/null || true

# Set ownership and permissions
echo "Setting permissions..."
sudo chown -R www-data:www-data $WEB_ROOT
sudo chmod -R 755 $WEB_ROOT

# Create symbolic links
echo "Creating symbolic links..."
sudo ln -sf $STATIC_DIR /root/Terminusa/static

# Update nginx user
echo "Configuring nginx..."
sudo sed -i 's/user root/user www-data/' /etc/nginx/nginx.conf

# Create nginx site configuration
sudo tee /etc/nginx/sites-available/terminusa.conf > /dev/null << 'EOF'
server {
    listen 80;
    server_name terminusa.online;

    # SSL configuration
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/terminusa.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/terminusa.online/privkey.pem;

    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$host$request_uri;
    }

    # Root directory
    root /var/www/terminusa;

    # Static files
    location /static/ {
        alias /var/www/terminusa/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
        add_header Access-Control-Allow-Origin "*";
        
        # Basic settings
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        
        # MIME type handling
        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        # Logging
        access_log /var/log/nginx/static-access.log combined buffer=32k flush=5s;
        error_log /var/log/nginx/static-error.log debug;
    }

    # Proxy all other requests to Flask
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    # WebSocket support
    location /socket.io {
        proxy_pass http://127.0.0.1:5001/socket.io;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; style-src 'self' https://fonts.googleapis.com https://cdnjs.cloudflare.com 'unsafe-inline';" always;

    # Logging
    access_log /var/log/nginx/terminusa.access.log combined buffer=32k flush=5s;
    error_log /var/log/nginx/terminusa.error.log debug;
}
EOF

# Enable site
echo "Enabling nginx site..."
sudo ln -sf /etc/nginx/sites-available/terminusa.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

# Restart services
echo "Restarting services..."
sudo systemctl restart nginx
sudo systemctl restart terminusa

echo "Setup complete!"
