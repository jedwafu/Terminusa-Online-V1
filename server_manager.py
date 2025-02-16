#!/usr/bin/env python3
import os
import sys
import time
import signal
import psutil
import logging
import subprocess
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

class ServiceManager:
    def __init__(self):
        self.console = Console()
        self.services = {
            'postgresql': {
                'name': 'PostgreSQL',
                'port': 5432,
                'start_cmd': 'systemctl start postgresql',
                'stop_cmd': 'systemctl stop postgresql',
                'status_cmd': 'systemctl status postgresql',
                'process_name': 'postgres'
            },
            'postfix': {
                'name': 'Mail Server',
                'port': 25,
                'start_cmd': 'systemctl start postfix',
                'stop_cmd': 'systemctl stop postfix',
                'status_cmd': 'systemctl status postfix',
                'process_name': 'master'
            },
            'opendkim': {
                'name': 'OpenDKIM',
                'start_cmd': 'systemctl start opendkim',
                'stop_cmd': 'systemctl stop opendkim',
                'status_cmd': 'systemctl status opendkim',
                'process_name': 'opendkim'
            },
            'game_server': {
                'name': 'Game Server',
                'port': int(os.getenv('SERVER_PORT', 5000)),
                'start_cmd': 'python main.py',
                'process_name': 'python'
            },
            'web_server': {
                'name': 'Web Server',
                'port': int(os.getenv('WEBAPP_PORT', 5001)),
                'start_cmd': 'python web_app.py',
                'process_name': 'python'
            }
        }
        self.processes = {}
        self.running = True
        self.layout = self._create_layout()

    def _create_layout(self):
        layout = Layout()
        layout.split_column(
            Layout(name="header"),
            Layout(name="main"),
            Layout(name="footer")
        )
        return layout

    def _get_process_info(self, process_name):
        """Get process information by name"""
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if process_name in proc.info['name']:
                    return proc.info
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return None

    def _check_port(self, port):
        """Check if a port is in use"""
        if not port:
            return True
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port:
                    return True
            return False
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return False

    def _create_status_table(self):
        """Create status table for services"""
        table = Table(title="Service Status")
        table.add_column("Service")
        table.add_column("Status")
        table.add_column("CPU %")
        table.add_column("Memory %")
        table.add_column("Port")

        for service_id, service in self.services.items():
            status = "🟢 Running" if self._get_process_info(service['process_name']) else "🔴 Stopped"
            proc_info = self._get_process_info(service['process_name'])
            cpu = f"{proc_info['cpu_percent']:.1f}%" if proc_info else "N/A"
            mem = f"{proc_info['memory_percent']:.1f}%" if proc_info else "N/A"
            port = str(service.get('port', 'N/A'))
            
            table.add_row(
                service['name'],
                status,
                cpu,
                mem,
                port
            )
        
        return table

    def start_service(self, service_id):
        """Start a specific service"""
        service = self.services.get(service_id)
        if not service:
            return False

        try:
            if service_id in ['game_server', 'web_server']:
                # Start Python services in new terminal
                process = subprocess.Popen(
                    service['start_cmd'].split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.processes[service_id] = process
            else:
                # Start system services
                subprocess.run(service['start_cmd'].split(), check=True)
            
            logger.info(f"Started {service['name']} on port {service.get('port', 'N/A')}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start {service['name']}: {e}")
            return False

    def stop_service(self, service_id):
        """Stop a specific service"""
        service = self.services.get(service_id)
        if not service:
            return False

        try:
            if service_id in ['game_server', 'web_server']:
                # Stop Python services
                process = self.processes.get(service_id)
                if process:
                    process.terminate()
                    process.wait(timeout=5)
            else:
                # Stop system services
                subprocess.run(service['stop_cmd'].split(), check=True)
            
            logger.info(f"Stopped {service['name']}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop {service['name']}: {e}")
            return False

    def start_all(self):
        """Start all services"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("Starting services...", total=len(self.services))
            
            # Start services in order
            for service_id in ['postgresql', 'postfix', 'opendkim', 'web_server', 'game_server']:
                self.start_service(service_id)
                progress.update(task, advance=1)
                time.sleep(1)  # Give each service time to start

    def stop_all(self):
        """Stop all services"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("Stopping services...", total=len(self.services))
            
            # Stop services in reverse order
            for service_id in ['game_server', 'web_server', 'opendkim', 'postfix', 'postgresql']:
                self.stop_service(service_id)
                progress.update(task, advance=1)
                time.sleep(1)  # Give each service time to stop

    def monitor(self):
        """Monitor all services"""
        try:
            with Live(self._create_status_table(), refresh_per_second=2) as live:
                while self.running:
                    live.update(self._create_status_table())
                    time.sleep(0.5)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Graceful shutdown of all services"""
        self.running = False
        self.console.print("\n[yellow]Shutting down services...[/yellow]")
        self.stop_all()
        self.console.print("[green]Shutdown complete![/green]")

def main():
    try:
        # Create logs directory
        os.makedirs('logs', exist_ok=True)

        # Initialize service manager
        manager = ServiceManager()

        # Start all services
        manager.start_all()

        # Monitor services
        manager.monitor()

    except KeyboardInterrupt:
        manager.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
