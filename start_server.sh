#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Terminusa Online Server...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

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
        apt-get update
        apt-get install -y postgresql postgresql-contrib
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        yum install -y postgresql-server postgresql-contrib
        postgresql-setup initdb
    else
        echo -e "${RED}Unsupported distribution. Please install PostgreSQL manually.${NC}"
        exit 1
    fi
fi

# Ensure PostgreSQL is running
if ! systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}Starting PostgreSQL service...${NC}"
    systemctl start postgresql
fi

# Check if Postfix is installed
if ! command -v postfix &> /dev/null; then
    echo -e "${RED}Postfix is not installed!${NC}"
    echo -e "${YELLOW}Installing Postfix...${NC}"
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        DEBIAN_FRONTEND=noninteractive apt-get install -y postfix
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        yum install -y postfix
    else
        echo -e "${RED}Unsupported distribution. Please install Postfix manually.${NC}"
        exit 1
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please update it with your configuration.${NC}"
    echo -e "${YELLOW}Press any key to continue after updating .env file...${NC}"
    read -n 1 -s
fi

# Create required directories
mkdir -p logs
mkdir -p instance

# Set proper permissions
chmod +x server_manager.py
chmod +x init_db.py

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python init_db.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Database initialization failed! Please check the logs.${NC}"
    exit 1
fi

# Start the server manager
echo -e "${GREEN}Starting server manager...${NC}"
python server_manager.py

# Keep the terminal open if there's an error
read -p "Press enter to continue..."
