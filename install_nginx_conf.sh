#!/bin/bash
# Script to install Nginx configuration for Terminusa Online

# Define the source and destination paths
SOURCE_CONF="/etc/nginx/sites-available/terminusa.conf"
DEST_CONF="/etc/nginx/sites-enabled/terminusa.conf"

# Copy the configuration file
if [ -f "$SOURCE_CONF" ]; then
    ln -sfn "$SOURCE_CONF" "$DEST_CONF"
    echo "Nginx configuration installed successfully."
else
    echo "Error: Nginx configuration file not found."
    exit 1
fi

# Restart Nginx
if sudo systemctl restart nginx; then
    echo "Nginx restarted successfully."
else
    echo "Error: Failed to restart Nginx."
    exit 1
fi
