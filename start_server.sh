#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if screen session exists
screen_exists() {
    screen -list | grep -q "$1"
}

# Function to create a new screen window
create_screen_window() {
    local session=$1
    local window=$2
    local command=$3
    screen -S $session -X screen -t "$window"
    screen -S $session -p "$window" -X stuff "$command$(printf \\r)"
}

echo -e "${GREEN}Starting Terminusa Online Server${NC}"

# Activate virtual environment if not already activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill existing screen session if it exists
if screen_exists "terminusa"; then
    echo -e "${YELLOW}Killing existing screen session...${NC}"
    screen -X -S terminusa quit
fi

# Start new screen session
echo -e "${YELLOW}Creating new screen session...${NC}"
screen -dmS terminusa

# Create screen windows with specific layouts and commands
echo -e "${YELLOW}Setting up screen windows...${NC}"

# Main server window
create_screen_window "terminusa" "main" "python main.py 2>&1 | tee logs/main.log"

# Game manager window
create_screen_window "terminusa" "game" "python game_manager.py 2>&1 | tee logs/game.log"

# Email monitor window
create_screen_window "terminusa" "email" "python email_monitor.py 2>&1 | tee logs/email.log"

# System monitor window (using htop if available)
if command -v htop >/dev/null 2>&1; then
    create_screen_window "terminusa" "system" "htop"
else
    create_screen_window "terminusa" "system" "top"
fi

# Log viewer window
create_screen_window "terminusa" "logs" "tail -f logs/*.log"

# Set up screen layout
screen -S terminusa -X layout new
screen -S terminusa -X layout save default

# Split screen vertically for main and game
screen -S terminusa -X split -v
screen -S terminusa -X focus right
screen -S terminusa -X select 1
screen -S terminusa -X focus left
screen -S terminusa -X select 0

# Split bottom half horizontally for email and system
screen -S terminusa -X split
screen -S terminusa -X focus down
screen -S terminusa -X select 2
screen -S terminusa -X split -v
screen -S terminusa -X focus right
screen -S terminusa -X select 3

# Add log viewer at the bottom
screen -S terminusa -X focus down
screen -S terminusa -X select 4

echo -e "${GREEN}Server started successfully!${NC}"
echo -e "${YELLOW}To attach to the screen session:${NC}"
echo -e "  ${GREEN}screen -r terminusa${NC}"
echo -e "${YELLOW}Screen windows:${NC}"
echo -e "  ${GREEN}0: Main Server${NC}"
echo -e "  ${GREEN}1: Game Manager${NC}"
echo -e "  ${GREEN}2: Email Monitor${NC}"
echo -e "  ${GREEN}3: System Monitor${NC}"
echo -e "  ${GREEN}4: Log Viewer${NC}"
echo -e "${YELLOW}Screen commands:${NC}"
echo -e "  ${GREEN}Ctrl+a c${NC}: Create new window"
echo -e "  ${GREEN}Ctrl+a n${NC}: Next window"
echo -e "  ${GREEN}Ctrl+a p${NC}: Previous window"
echo -e "  ${GREEN}Ctrl+a d${NC}: Detach from screen"
echo -e "  ${GREEN}Ctrl+a ?${NC}: Help"

# Automatically attach to the screen session
exec screen -r terminusa
