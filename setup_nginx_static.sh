#!/bin/bash

# Set up directories
PROJECT_DIR="/root/Terminusa"
STATIC_DIR="$PROJECT_DIR/static"

# Create static directories if they don't exist
mkdir -p "$STATIC_DIR/css"
mkdir -p "$STATIC_DIR/js"
mkdir -p "$STATIC_DIR/images"

# Set ownership and permissions
chown -R www-data:www-data "$STATIC_DIR"
chmod -R 755 "$STATIC_DIR"

# Ensure nginx has access to the project directory
chmod 755 "$PROJECT_DIR"

# Restart nginx
systemctl restart nginx

# Test nginx configuration
nginx -t

echo "Static files have been set up for nginx"
echo "Testing nginx configuration..."

# Check if nginx test was successful
if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid"
else
    echo "Error in nginx configuration"
fi
