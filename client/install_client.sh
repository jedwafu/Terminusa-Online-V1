#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Terminusa Online Client${NC}"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv-client

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv-client/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing client dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements-client.txt

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}To run the client:${NC}"
echo -e "1. Activate the virtual environment: ${GREEN}source venv-client/bin/activate${NC}"
echo -e "2. Run the client: ${GREEN}python client.py${NC}"

# Make the script executable
chmod +x client.py
