#!/bin/bash

# Enable UFW if not already enabled
sudo ufw enable

# Allow SSH (port 22) to prevent lockout
sudo ufw allow 22/tcp

# Allow HTTP (port 80)
sudo ufw allow 80/tcp

# Allow HTTPS (port 443)
sudo ufw allow 443/tcp

# Allow game server port (5000)
sudo ufw allow 5000/tcp

# Allow email ports
sudo ufw allow 25/tcp   # SMTP
sudo ufw allow 465/tcp  # SMTPS
sudo ufw allow 587/tcp  # Submission

# Allow web app port (5001)
sudo ufw allow 5001/tcp

# Reload UFW to apply changes
sudo ufw reload

# Show status
sudo ufw status verbose
