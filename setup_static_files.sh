#!/bin/bash

# Create static files directory if it doesn't exist
sudo mkdir -p /var/www/terminusa/static
sudo mkdir -p /var/www/terminusa/static/css
sudo mkdir -p /var/www/terminusa/static/js
sudo mkdir -p /var/www/terminusa/static/images

# Copy static files to the new location
sudo cp -r static/* /var/www/terminusa/static/

# Set proper ownership and permissions
sudo chown -R www-data:www-data /var/www/terminusa
sudo chmod -R 755 /var/www/terminusa

# Create symbolic link
sudo ln -sf /var/www/terminusa/static /root/Terminusa/static

# Restart nginx
sudo systemctl restart nginx

echo "Static files have been set up"
