#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import signal
import logging
import psutil
from datetime import datetime
import threading
import json
from typing import Dict, List, Optional

class ServerManager:
    def __init__(self):
        self.setup_logging()
        self.processes: Dict[str, subprocess.Popen] = {}
        self.should_run = True
        self.status = {
            'game_server': 'stopped',
            'email_monitor': 'stopped',
            'postfix': 'stopped',
            'opendkim': 'stopped'
        }

    def setup_logging(self):
        """Set up logging configuration"""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        self.logger = logging.getLogger('server_manager')
        handler = logging.FileHandler('logs/server_manager.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Also log to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        try:
            # Check Python packages
            self.logger.info("Checking Python dependencies...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         check=True)

            # Check system services
            self.logger.info("Checking system services...")
            services = ['postfix', 'opendkim']
            for service in services:
                result = subprocess.run(['systemctl', 'is-active', service], 
                                     capture_output=True, text=True)
                if 'active' not in result.stdout:
                    self.logger.error(f"{service} is not running")
                    return False

            return True
        except Exception as e:
            self.logger.error(f"Dependency check failed: {e}")
            return False

    def start_email_services(self) -> bool:
        """Start email-related services"""
        try:
            self.logger.info("Starting email services...")
            services = ['postfix', 'opendkim']
            for service in services:
                subprocess.run(['sudo', 'systemctl', 'restart', service], check=True)
                self.status[service] = 'running'
            return True
        except Exception as e:
            self.logger.error(f"Failed to start email services: {e}")
            return False

    def start_email_monitor(self):
        """Start email monitoring service"""
        try:
            self.logger.info("Starting email monitor...")
            monitor_process = subprocess.Popen(
                [sys.executable, 'email_monitor.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.processes['email_monitor'] = monitor_process
            self.status['email_monitor'] = 'running'
            
            # Log process output
            threading.Thread(target=self.log_process_output, 
                           args=(monitor_process, 'email_monitor')).start()
        except Exception as e:
            self.logger.error(f"Failed to start email monitor: {e}")

    def start_game_server(self):
        """Start the main game server"""
        try:
            self.logger.info("Starting game server...")
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"  # Ensure Python output is unbuffered
            
            server_process = subprocess.Popen(
                [sys.executable, 'main.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env
            )
            self.processes['game_server'] = server_process
            self.status['game_server'] = 'running'
            
            # Log process output
            threading.Thread(target=self.log_process_output, 
                           args=(server_process, 'game_server')).start()
            
            # Wait a bit to ensure server starts
            time.sleep(5)
            
            # Check if process is still running
            if server_process.poll() is not None:
                self.logger.error("Game server failed to start!")
                return False
                
            self.logger.info("Game server started successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start game server: {e}")
            return False

    def log_process_output(self, process: subprocess.Popen, name: str):
        """Log process output in real-time"""
        while True:
            if process.poll() is not None:
                break
                
            output = process.stdout.readline()
            if output:
                self.logger.info(f"[{name}] {output.strip()}")
                
            error = process.stderr.readline()
            if error:
                self.logger.error(f"[{name}] {error.strip()}")

    def monitor_processes(self):
        """Monitor running processes"""
        while self.should_run:
            try:
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        self.logger.error(f"{name} has stopped. Restarting...")
                        self.status[name] = 'restarting'
                        if name == 'game_server':
                            self.start_game_server()
                        elif name == 'email_monitor':
                            self.start_email_monitor()
                
                # Check system services
                for service in ['postfix', 'opendkim']:
                    result = subprocess.run(['systemctl', 'is-active', service], 
                                         capture_output=True, text=True)
                    if 'active' not in result.stdout:
                        self.logger.error(f"{service} is not running. Restarting...")
                        self.status[service] = 'restarting'
                        subprocess.run(['sudo', 'systemctl', 'restart', service])
                    else:
                        self.status[service] = 'running'

                # Save status to file
                self.save_status()
                
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in process monitor: {e}")
                time.sleep(5)

    def save_status(self):
        """Save current status to file"""
        try:
            status_data = {
                'timestamp': datetime.now().isoformat(),
                'services': self.status,
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent
                }
            }
            with open('server_status.json', 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving status: {e}")

    def start(self):
        """Start all services"""
        self.logger.info("Starting Terminusa Online server...")
        
        if not self.check_dependencies():
            self.logger.error("Dependency check failed. Aborting startup.")
            return False

        if not self.start_email_services():
            self.logger.error("Failed to start email services. Aborting startup.")
            return False

        self.start_email_monitor()
        if not self.start_game_server():
            self.logger.error("Failed to start game server. Aborting startup.")
            return False

        # Start process monitor
        self.monitor_thread = threading.Thread(target=self.monitor_processes)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        self.logger.info("All services started successfully!")
        return True

    def stop(self):
        """Stop all services gracefully"""
        self.logger.info("Stopping all services...")
        self.should_run = False
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            self.status[name] = 'stopped'

        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()

        self.save_status()
        self.logger.info("All services stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutting down gracefully...")
    server_manager.stop()
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server_manager = ServerManager()
    
    if server_manager.start():
        print("Terminusa Online server started successfully!")
        print("Press Ctrl+C to stop all services gracefully")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            server_manager.stop()
    else:
        print("Failed to start server. Check logs for details.")
        sys.exit(1)
