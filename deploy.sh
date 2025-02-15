#!/bin/bash

# Configuration
REPO_URL="https://github.com/jedwafu/Terminusa-Online-V1.git"
INSTALL_DIR="/root/Terminusa"

# Check if directory exists and is a git repository
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Directory does not exist. Cloning repository..."
    git clone $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
elif [ ! -d "$INSTALL_DIR/.git" ]; then
    echo "Directory exists but is not a git repository. Reinitializing..."
    rm -rf $INSTALL_DIR/*
    git clone $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
else
    echo "Directory exists. Pulling updates..."
    cd $INSTALL_DIR
    git pull origin main
fi

# Install/update dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing/updating dependencies..."
    pip install -r requirements.txt
fi

echo "Deployment completed!"
