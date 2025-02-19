#!/bin/bash

# Set ownership and permissions for static files
sudo chown -R root:root /root/Terminusa/static
sudo chmod -R 755 /root/Terminusa/static

# Restart nginx to apply changes
sudo systemctl restart nginx

echo "Static file permissions have been updated"
