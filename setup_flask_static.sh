#!/bin/bash

# Set up static directory structure
STATIC_DIR="/root/Terminusa/static"

# Create directories
mkdir -p "$STATIC_DIR/css"
mkdir -p "$STATIC_DIR/js"
mkdir -p "$STATIC_DIR/images"

# Copy all CSS files
cp -r static/css/* "$STATIC_DIR/css/"

# Copy all JS files
cp -r static/js/* "$STATIC_DIR/js/"

# Copy all image files
cp -r static/images/* "$STATIC_DIR/images/" 2>/dev/null || true

# Set permissions
chown -R www-data:www-data "$STATIC_DIR"
chmod -R 755 "$STATIC_DIR"

# Create symbolic link if needed
ln -sf "$STATIC_DIR" /var/www/terminusa/static

# Restart Flask application
systemctl restart terminusa

echo "Static files have been set up for Flask"
