#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Terminusa Client...${NC}"

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
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Make client executable
chmod +x client.py

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}To start the client:${NC}"
echo -e "1. Activate the virtual environment: ${GREEN}source venv/bin/activate${NC}"
echo -e "2. Run the client: ${GREEN}./client.py${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOL
# Server Configuration
API_URL=http://46.250.228.210:5000
DEBUG=False

# Client Configuration
CLIENT_VERSION=1.0.0
EOL
    echo -e "${GREEN}.env file created${NC}"
fi
