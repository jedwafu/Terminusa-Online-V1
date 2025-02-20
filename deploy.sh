#!/bin/bash

# ... (keep all previous content until enhanced_monitor_services function)

# Show menu function
show_menu() {
    while true; do
        clear
        echo -e "${CYAN}=== Terminusa Online Management ===${NC}"
        echo
        echo "1) Deploy/Update System"
        echo "2) Start All Services"
        echo "3) Stop All Services"
        echo "4) Restart All Services"
        echo "5) Enhanced Monitoring"
        echo "6) View Logs"
        echo "7) Database Operations"
        echo "8) Game Systems"
        echo "9) System Status"
        echo "10) Port Management"
        echo "11) Debug Mode"
        echo "0) Exit"
        echo
        read -p "Select an option: " choice
        
        case $choice in
            1)
                initialize_deployment
                ;;
            2)
                start_services
                ;;
            3)
                stop_services
                ;;
            4)
                stop_services
                sleep 2
                start_services
                ;;
            5)
                enhanced_monitor_services
                ;;
            6)
                echo -e "\n${YELLOW}Available Logs:${NC}"
                echo "1) Flask App Log"
                echo "2) Terminal Server Log"
                echo "3) Game Server Log"
                echo "4) Email Monitor Log"
                echo "5) AI Manager Log"
                echo "6) Combat Manager Log"
                echo "7) Economy Systems Log"
                echo "8) Game Mechanics Log"
                echo "9) Nginx Error Log"
                echo "10) Nginx Access Log"
                echo "11) PostgreSQL Log"
                echo "12) Redis Log"
                echo "13) Service Status Log"
                echo "0) Back to main menu"
                read -p "Select log to view: " log_choice
                case $log_choice in
                    1) tail -f logs/flask.log ;;
                    2) tail -f logs/terminal.log ;;
                    3) tail -f logs/game.log ;;
                    4) tail -f logs/email_monitor.log ;;
                    5) tail -f logs/ai_manager.log ;;
                    6) tail -f logs/combat_manager.log ;;
                    7) tail -f logs/economy_systems.log ;;
                    8) tail -f logs/game_mechanics.log ;;
                    9) tail -f /var/log/nginx/error.log ;;
                    10) tail -f /var/log/nginx/access.log ;;
                    11) tail -f /var/log/postgresql/postgresql-main.log ;;
                    12) tail -f /var/log/redis/redis-server.log ;;
                    13) cat logs/service_status.json | python3 -m json.tool ;;
                    0) continue ;;
                    *) error_log "Invalid option" ;;
                esac
                ;;
            7)
                echo -e "\n${YELLOW}Database Operations:${NC}"
                echo "1) Check Database Status"
                echo "2) Run Migrations"
                echo "3) Initialize Game Data"
                echo "4) Backup Database"
                echo "5) Restore Database"
                echo "6) Reset Database"
                echo "0) Back to main menu"
                read -p "Select operation: " db_choice
                case $db_choice in
                    1) 
                        source venv/bin/activate
                        python scripts/manage_db.py check
                        ;;
                    2)
                        source venv/bin/activate
                        python scripts/manage_db.py migrate
                        ;;
                    3)
                        source venv/bin/activate
                        python scripts/init_game_data.py
                        ;;
                    4)
                        source venv/bin/activate
                        python scripts/manage_db.py backup
                        ;;
                    5)
                        echo -e "\n${YELLOW}Available backups:${NC}"
                        ls -1 backups/
                        read -p "Enter backup file name: " backup_file
                        if [ -f "backups/$backup_file" ]; then
                            source venv/bin/activate
                            python scripts/manage_db.py restore "backups/$backup_file"
                        else
                            error_log "Backup file not found"
                        fi
                        ;;
                    6)
                        read -p "Are you sure? This will delete all data! (y/N) " confirm
                        if [ "$confirm" = "y" ]; then
                            source venv/bin/activate
                            python scripts/manage_db.py reset
                        fi
                        ;;
                    0) continue ;;
                    *) error_log "Invalid option" ;;
                esac
                ;;
            8)
                echo -e "\n${YELLOW}Game Systems:${NC}"
                echo "1) AI Management"
                echo "2) Combat & Gates"
                echo "3) Economy & Market"
                echo "4) Social Systems"
                echo "5) Data Management"
                echo "0) Back to main menu"
                read -p "Select system: " game_choice
                case $game_choice in
                    1)
                        echo -e "\n${YELLOW}AI Management:${NC}"
                        echo "1) Train Models"
                        echo "2) Evaluate Models"
                        echo "3) Analyze Player"
                        echo "4) Adjust Rates"
                        echo "5) Export Stats"
                        echo "0) Back"
                        read -p "Select operation: " ai_choice
                        case $ai_choice in
                            1)
                                read -p "Enter model name: " model_name
                                source venv/bin/activate
                                python scripts/manage_ai.py train "$model_name"
                                ;;
                            2)
                                read -p "Enter model name: " model_name
                                source venv/bin/activate
                                python scripts/manage_ai.py evaluate "$model_name"
                                ;;
                            3)
                                read -p "Enter character ID: " char_id
                                source venv/bin/activate
                                python scripts/manage_ai.py analyze "$char_id"
                                ;;
                            4)
                                source venv/bin/activate
                                python scripts/manage_ai.py adjust gacha
                                python scripts/manage_ai.py adjust gambling
                                ;;
                            5)
                                source venv/bin/activate
                                python scripts/manage_ai.py export
                                ;;
                            0) continue ;;
                            *) error_log "Invalid option" ;;
                        esac
                        ;;
                    2)
                        echo -e "\n${YELLOW}Combat & Gates:${NC}"
                        echo "1) Check Gates"
                        echo "2) Analyze Combat"
                        echo "3) Manage Beasts"
                        echo "4) Export Data"
                        echo "0) Back"
                        read -p "Select operation: " combat_choice
                        case $combat_choice in
                            1)
                                source venv/bin/activate
                                python scripts/manage_combat.py gates
                                ;;
                            2)
                                source venv/bin/activate
                                python scripts/manage_combat.py combat
                                ;;
                            3)
                                source venv/bin/activate
                                python scripts/manage_combat.py beasts
                                ;;
                            4)
                                source venv/bin/activate
                                python scripts/manage_combat.py export
                                ;;
                            0) continue ;;
                            *) error_log "Invalid option" ;;
                        esac
                        ;;
                    3)
                        echo -e "\n${YELLOW}Economy & Market:${NC}"
                        echo "1) Check Currency Supply"
                        echo "2) Analyze Market"
                        echo "3) Adjust Prices"
                        echo "4) Export Data"
                        echo "0) Back"
                        read -p "Select operation: " economy_choice
                        case $economy_choice in
                            1)
                                source venv/bin/activate
                                python scripts/manage_economy.py supply
                                ;;
                            2)
                                source venv/bin/activate
                                python scripts/manage_economy.py market
                                ;;
                            3)
                                source venv/bin/activate
                                python scripts/manage_economy.py prices
                                ;;
                            4)
                                source venv/bin/activate
                                python scripts/manage_economy.py export
                                ;;
                            0) continue ;;
                            *) error_log "Invalid option" ;;
                        esac
                        ;;
                    4)
                        echo -e "\n${YELLOW}Social Systems:${NC}"
                        echo "1) Check Guilds"
                        echo "2) Analyze Parties"
                        echo "3) Manage Quests"
                        echo "4) Export Data"
                        echo "0) Back"
                        read -p "Select operation: " social_choice
                        case $social_choice in
                            1)
                                source venv/bin/activate
                                python scripts/manage_social.py guilds
                                ;;
                            2)
                                source venv/bin/activate
                                python scripts/manage_social.py parties
                                ;;
                            3)
                                source venv/bin/activate
                                python scripts/manage_social.py quests
                                ;;
                            4)
                                source venv/bin/activate
                                python scripts/manage_social.py export
                                ;;
                            0) continue ;;
                            *) error_log "Invalid option" ;;
                        esac
                        ;;
                    5)
                        echo -e "\n${YELLOW}Data Management:${NC}"
                        echo "1) Setup Directories"
                        echo "2) Cleanup Old Data"
                        echo "3) Analyze Usage"
                        echo "4) Export Info"
                        echo "0) Back"
                        read -p "Select operation: " data_choice
                        case $data_choice in
                            1)
                                source venv/bin/activate
                                python scripts/manage_data.py setup
                                ;;
                            2)
                                read -p "Remove files older than days (default 30): " days
                                days=${days:-30}
                                source venv/bin/activate
                                python scripts/manage_data.py cleanup --days "$days"
                                ;;
                            3)
                                source venv/bin/activate
                                python scripts/manage_data.py analyze
                                ;;
                            4)
                                source venv/bin/activate
                                python scripts/manage_data.py export
                                ;;
                            0) continue ;;
                            *) error_log "Invalid option" ;;
                        esac
                        ;;
                    0) continue ;;
                    *) error_log "Invalid option" ;;
                esac
                ;;
            9)
                bash status_monitor.sh
                ;;
            10)
                echo -e "\n${YELLOW}Port Management:${NC}"
                echo "1) Check Port Status"
                echo "2) Kill Process on Port"
                echo "3) Show All Used Ports"
                echo "0) Back to main menu"
                read -p "Select operation: " port_choice
                case $port_choice in
                    1)
                        read -p "Enter port number: " port
                        show_port_status $port
                        ;;
                    2)
                        read -p "Enter port number: " port
                        kill_port_process $port
                        ;;
                    3)
                        netstat -tulpn | grep LISTEN
                        ;;
                    0) continue ;;
                    *) error_log "Invalid option" ;;
                esac
                ;;
            11)
                if [ "$DEBUG" = true ]; then
                    DEBUG=false
                    info_log "Debug mode disabled"
                else
                    DEBUG=true
                    info_log "Debug mode enabled"
                fi
                ;;
            0)
                info_log "Exiting..."
                exit 0
                ;;
            *)
                error_log "Invalid option"
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Trap signals for graceful shutdown
trap 'MONITOR_RUNNING=false; stop_services; exit 0' SIGINT SIGTERM

# Main execution
mkdir -p logs
show_menu
