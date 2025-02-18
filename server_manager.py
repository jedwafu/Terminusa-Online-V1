#!/usr/bin/env python3
import os
import sys
import time
import signal
import psutil
import logging
import subprocess
import bcrypt
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from dotenv import load_dotenv
from app_final import app
from models import User, PlayerCharacter, Wallet, Inventory
from database import db, init_db
import requests

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
            'nginx': {
                'name': 'Nginx',
                'port': 80,
                'start_cmd': 'systemctl start nginx',
                'stop_cmd': 'systemctl stop nginx',
                'status_cmd': 'systemctl status nginx',
                'process_name': 'nginx'
            },
            'gunicorn': {
                'name': 'Gunicorn',
                'port': 8000,
                'start_cmd': 'gunicorn -w 4 -b 0.0.0.0:8000 app_final:app',
                'process_name': 'gunicorn'
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
                'process_name': 'python',
                'health_url': 'http://localhost:5000/health'
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

    def _check_service_health(self, url):
        """Check service health by URL"""
        try:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def _create_status_table(self):
        """Create status table for services"""
        table = Table(title="Service Status")
        table.add_column("Service")
        table.add_column("Status")
        table.add_column("CPU %")
        table.add_column("Memory %")
        table.add_column("Port")
        table.add_column("Health")

        for service_id, service in self.services.items():
            status = "🟢 Running" if self._get_process_info(service['process_name']) else "🔴 Stopped"
            proc_info = self._get_process_info(service['process_name'])
            cpu = f"{proc_info['cpu_percent']:.1f}%" if proc_info else "N/A"
            mem = f"{proc_info['memory_percent']:.1f}%" if proc_info else "N/A"
            port = str(service.get('port', 'N/A'))
            
            health = "N/A"
            if service.get('health_url') and status == "🟢 Running":
                health = "🟢 Healthy" if self._check_service_health(service['health_url']) else "🔴 Unhealthy"
            
            table.add_row(
                service['name'],
                status,
                cpu,
                mem,
                port,
                health
            )
        
        return table

    def start_service(self, service_id):
        """Start a specific service"""
        service = self.services.get(service_id)
        if not service:
            return False

        try:
            if service_id in ['game_server', 'gunicorn']:
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
            
            # Wait for service to be ready
            max_attempts = 30
            attempt = 0
            while attempt < max_attempts:
                if service.get('health_url'):
                    if self._check_service_health(service['health_url']):
                        break
                elif service.get('port'):
                    if self._check_port(service['port']):
                        break
                attempt += 1
                time.sleep(1)
            
            if attempt == max_attempts:
                logger.error(f"Service {service['name']} failed to start properly")
                return False
            
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
            if service_id in ['game_server', 'gunicorn']:
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
            task = progress.add_task("Starting services...", total=len(self.services) + 2)  # +2 for db init and admin check
            
            # Initialize database first
            self.console.print("[yellow]Initializing database...[/yellow]")
            with app.app_context():
                # Initialize database
                init_db(app)
                
                # Ensure admin account exists
                if not ensure_admin_exists():
                    self.console.print("[red]Failed to ensure admin account exists![/red]")
                    return False
            progress.update(task, advance=2)
            
            # Start services in order
            service_order = [
                'postgresql',
                'nginx',
                'postfix',
                'opendkim',
                'gunicorn',
                'game_server'
            ]
            
            for service_id in service_order:
                if not self.start_service(service_id):
                    self.console.print(f"[red]Failed to start {service_id}![/red]")
                    return False
                progress.update(task, advance=1)
                time.sleep(1)  # Give each service time to start

            return True

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
            service_order = [
                'game_server',
                'gunicorn',
                'opendkim',
                'postfix',
                'nginx',
                'postgresql'
            ]
            
            for service_id in service_order:
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

def ensure_admin_exists():
    """Ensure admin account exists"""
    try:
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.info("Admin account already exists")
            return True

        # Create admin user
        logger.info("Creating admin account...")
        password = "admin123"
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

        admin = User(
            username='admin',
            email='admin@terminusa.online',
            password=password_hash.decode('utf-8'),
            salt=salt.decode('utf-8'),
            role='admin',
            is_email_verified=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        db.session.add(admin)
        db.session.commit()  # Commit to get admin.id

        # Create admin character
        character = PlayerCharacter(
            user_id=admin.id,
            level=100,
            experience=0,
            rank='S',
            title='Administrator',
            strength=100,
            agility=100,
            intelligence=100,
            vitality=100,
            wisdom=100,
            hp=1000,
            mp=1000,
            physical_attack=100,
            magical_attack=100,
            physical_defense=100,
            magical_defense=100
        )
        db.session.add(character)
        db.session.commit()

        # Create admin wallet
        wallet = Wallet(
            user_id=admin.id,
            address=f"wallet_{os.urandom(8).hex()}",
            encrypted_privkey=os.urandom(32).hex(),
            iv=os.urandom(16).hex(),
            sol_balance=1000.0,
            crystals=100000,
            exons=100000
        )
        db.session.add(wallet)
        db.session.commit()

        # Create admin inventory
        inventory = Inventory(
            user_id=admin.id,
            max_slots=1000
        )
        db.session.add(inventory)
        db.session.commit()

        logger.info("Admin account created successfully")
        return True

    except Exception as e:
        logger.error(f"Error ensuring admin account: {str(e)}")
        db.session.rollback()
        return False

def main():
    try:
        # Create logs directory
        os.makedirs('logs', exist_ok=True)

        # Initialize service manager
        manager = ServiceManager()

        # Start all services
        if manager.start_all():
            # Monitor services
            manager.monitor()
        else:
            logger.error("Failed to start all services")
            sys.exit(1)

    except KeyboardInterrupt:
        manager.shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
