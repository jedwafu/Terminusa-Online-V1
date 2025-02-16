#!/usr/bin/env python3
import os
import sys
import subprocess
import signal
import time
import psutil
import logging
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

console = Console()

class ServerManager:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Create necessary directories
        os.makedirs('logs', exist_ok=True)
        
        # Initialize process tracking
        self.processes = {}
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def start_postgresql(self):
        """Start PostgreSQL database server"""
        try:
            console.print("[yellow]Starting PostgreSQL...[/yellow]")
            
            # Check if PostgreSQL is already running
            if self.check_port_in_use(5432):
                console.print("[green]PostgreSQL is already running[/green]")
                return True
            
            # Start PostgreSQL
            if os.name == 'nt':  # Windows
                cmd = ['pg_ctl', 'start', '-D', os.getenv('PGDATA', 'data')]
            else:  # Linux/Unix
                cmd = ['sudo', '-u', 'postgres', 'pg_ctl', 'start', '-D', '/var/lib/postgresql/data']
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['postgresql'] = process
            
            # Wait for PostgreSQL to start
            time.sleep(5)
            if self.check_port_in_use(5432):
                console.print("[green]PostgreSQL started successfully[/green]")
                return True
            else:
                console.print("[red]Failed to start PostgreSQL[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]Error starting PostgreSQL: {str(e)}[/red]")
            return False

    def start_email_service(self):
        """Start the email service"""
        try:
            console.print("[yellow]Starting Email Service...[/yellow]")
            
            # Check if email service port is in use
            email_port = int(os.getenv('EMAIL_PORT', 587))
            if self.check_port_in_use(email_port):
                console.print("[green]Email Service is already running[/green]")
                return True
            
            cmd = [sys.executable, 'email_service.py']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['email'] = process
            
            time.sleep(2)
            if process.poll() is None:
                console.print("[green]Email Service started successfully[/green]")
                return True
            else:
                console.print("[red]Failed to start Email Service[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]Error starting Email Service: {str(e)}[/red]")
            return False

    def start_web_server(self):
        """Start the web server"""
        try:
            console.print("[yellow]Starting Web Server...[/yellow]")
            
            # Check if web server port is in use
            web_port = int(os.getenv('WEBAPP_PORT', 3000))
            if self.check_port_in_use(web_port):
                console.print("[green]Web Server is already running[/green]")
                return True
            
            cmd = [sys.executable, 'web_app.py']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['web'] = process
            
            time.sleep(2)
            if process.poll() is None:
                console.print("[green]Web Server started successfully[/green]")
                return True
            else:
                console.print("[red]Failed to start Web Server[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]Error starting Web Server: {str(e)}[/red]")
            return False

    def start_game_server(self):
        """Start the game server"""
        try:
            console.print("[yellow]Starting Game Server...[/yellow]")
            
            # Check if game server port is in use
            game_port = int(os.getenv('SERVER_PORT', 5000))
            if self.check_port_in_use(game_port):
                console.print("[green]Game Server is already running[/green]")
                return True
            
            cmd = [sys.executable, 'main.py']
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['game'] = process
            
            time.sleep(2)
            if process.poll() is None:
                console.print("[green]Game Server started successfully[/green]")
                return True
            else:
                console.print("[red]Failed to start Game Server[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]Error starting Game Server: {str(e)}[/red]")
            return False

    @staticmethod
    def check_port_in_use(port):
        """Check if a port is in use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def monitor_processes(self):
        """Monitor running processes and restart if needed"""
        while self.running:
            for name, process in self.processes.items():
                if process.poll() is not None:
                    console.print(f"[yellow]Warning: {name} has stopped, attempting to restart...[/yellow]")
                    if name == 'postgresql':
                        self.start_postgresql()
                    elif name == 'email':
                        self.start_email_service()
                    elif name == 'web':
                        self.start_web_server()
                    elif name == 'game':
                        self.start_game_server()
            time.sleep(5)

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        self.running = False
        console.print("\n[yellow]Shutting down services...[/yellow]")
        
        # Stop all processes
        for name, process in self.processes.items():
            try:
                console.print(f"[yellow]Stopping {name}...[/yellow]")
                if os.name == 'nt':  # Windows
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)])
                else:  # Linux/Unix
                    process.terminate()
                    process.wait(timeout=5)
            except Exception as e:
                console.print(f"[red]Error stopping {name}: {str(e)}[/red]")

        # Stop PostgreSQL specifically
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['pg_ctl', 'stop', '-D', os.getenv('PGDATA', 'data')])
            else:  # Linux/Unix
                subprocess.run(['sudo', '-u', 'postgres', 'pg_ctl', 'stop', '-D', '/var/lib/postgresql/data'])
        except Exception as e:
            console.print(f"[red]Error stopping PostgreSQL: {str(e)}[/red]")

        console.print("[green]All services stopped[/green]")
        sys.exit(0)

    def start_all(self):
        """Start all services"""
        with Progress() as progress:
            task = progress.add_task("[cyan]Starting services...", total=4)
            
            # Start PostgreSQL
            if self.start_postgresql():
                progress.update(task, advance=1)
            
            # Start Email Service
            if self.start_email_service():
                progress.update(task, advance=1)
            
            # Start Web Server
            if self.start_web_server():
                progress.update(task, advance=1)
            
            # Start Game Server
            if self.start_game_server():
                progress.update(task, advance=1)

        if len(self.processes) == 4:
            console.print(Panel.fit(
                "[green]All services started successfully![/green]\n"
                f"PostgreSQL: Running on port 5432\n"
                f"Email Service: Running on port {os.getenv('EMAIL_PORT', 587)}\n"
                f"Web Server: Running on port {os.getenv('WEBAPP_PORT', 3000)}\n"
                f"Game Server: Running on port {os.getenv('SERVER_PORT', 5000)}"
            ))
            return True
        else:
            console.print("[red]Some services failed to start[/red]")
            return False

def main():
    try:
        manager = ServerManager()
        if manager.start_all():
            console.print("\n[yellow]Press Ctrl+C to stop all services[/yellow]")
            manager.monitor_processes()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
