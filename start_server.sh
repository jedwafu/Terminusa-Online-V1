#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Terminusa Online Server...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python is not installed! Please install Python 3.10 or later.${NC}"
    exit 1
fi

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
echo -e "${YELLOW}Installing/Updating dependencies...${NC}"
pip install -r requirements-base.txt

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL is not installed!${NC}"
    echo -e "${YELLOW}Installing PostgreSQL...${NC}"
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        sudo yum install -y postgresql-server postgresql-contrib
        sudo postgresql-setup initdb
    else
        echo -e "${RED}Unsupported distribution. Please install PostgreSQL manually.${NC}"
        exit 1
    fi
fi

# Ensure PostgreSQL is running
if ! systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}Starting PostgreSQL service...${NC}"
    sudo systemctl start postgresql
fi

# Make script executable
chmod +x run_server.py

# Start the server
echo -e "${GREEN}Starting server...${NC}"
python run_server.py

# Keep the terminal open if there's an error
read -p "Press enter to continue..."
