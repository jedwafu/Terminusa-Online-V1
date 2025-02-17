#!/usr/bin/env python3
import os
import sys
import cmd
import json
import requests
import getpass
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn
from rich.live import Live
from rich.layout import Layout
import time
import asyncio
from urllib.parse import urljoin
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()

# ASCII Art
TITLE_ART = """
╔══════════════════════════════════════════════════════════════════════════╗
║     ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗██╗   ██╗███████╗ ║
║     ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██║   ██║██╔════╝ ║
║        ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║██║   ██║███████╗ ║
║        ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██║   ██║╚════██║ ║
║        ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝███████║ ║
║        ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ║
║                                                                          ║
║                         [cyan]ARISE[/cyan] - Online                              ║
║                                                                          ║
║                    [red]"I Alone Level Up"[/red]                               ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

class TerminusaClient(cmd.Cmd):
    intro = TITLE_ART + """
[cyan]Welcome to the System[/cyan]

[green]Available Commands:[/green]
  login     - Enter the System
  register  - Join as a New Hunter
  help      - View All Commands
  quit      - Exit the System

[red]"Only the strong survive in this world."[/red]
"""
    prompt = '[bold blue]>>>[/bold blue] '
    
    def __init__(self):
        super().__init__()
        self.token = None
        self.user_data = None
        self.character = None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'TerminusaClient/1.0'})
        
        # Server configuration
        self.base_url = 'http://46.250.228.210:5000'
        
        # Initialize console layout
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Test server connection
        self._test_server_connection()
        
    def _test_server_connection(self):
        """Test connection to the server"""
        try:
            with Progress(
                "[progress.description]{task.description}",
                SpinnerColumn(),
                transient=True,
            ) as progress:
                task = progress.add_task("[cyan]Establishing connection to the System...[/cyan]", total=None)
                response = self.session.get(urljoin(self.base_url, '/health'), timeout=5)
                
            if response.status_code == 200:
                console.print(Panel.fit(
                    "[green]Connection established successfully.[/green]",
                    title="System Status",
                    border_style="green"
                ))
            else:
                console.print(Panel.fit(
                    f"[red]System not responding correctly (Status: {response.status_code})[/red]",
                    title="System Status",
                    border_style="red"
                ))
        except requests.exceptions.ConnectionError:
            console.print(Panel.fit(
                f"[red]Failed to connect to System at {self.base_url}[/red]\n"
                "[yellow]Please verify System status and connection details.[/yellow]",
                title="Connection Error",
                border_style="red"
            ))
        except Exception as e:
            console.print(Panel.fit(
                f"[red]System connection error: {str(e)}[/red]",
                title="Error",
                border_style="red"
            ))

    def _make_request(self, method, endpoint, **kwargs):
        """Make a request to the server with proper error handling"""
        try:
            url = urljoin(self.base_url, endpoint)
            timeout = kwargs.pop('timeout', 10)
            
            if self.token:
                kwargs.setdefault('headers', {})
                kwargs['headers']['Authorization'] = f'Bearer {self.token}'
            
            with Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                transient=True,
            ) as progress:
                task = progress.add_task("[cyan]Processing request...[/cyan]", total=None)
                response = self.session.request(method, url, timeout=timeout, **kwargs)
            
            if response.status_code == 401:
                self.token = None
                self.user_data = None
                self.character = None
                raise Exception("Authentication failed. Please login again.")
            elif response.status_code == 403:
                raise Exception("Access denied. Insufficient permissions.")
            elif response.status_code == 404:
                raise Exception("Requested resource not found.")
            elif response.status_code >= 500:
                raise Exception("System error. Please try again later.")
            
            return response
        except requests.exceptions.ConnectionError:
            raise Exception(f"Connection lost: Unable to reach System at {self.base_url}")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. System not responding.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def do_login(self, arg):
        """Enter the System"""
        console.print("\n[cyan]System Authentication Required[/cyan]")
        username = Prompt.ask("[cyan]Hunter ID[/cyan]")
        password = getpass.getpass("[cyan]Access Code: [/cyan]")
        
        try:
            with Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                transient=True,
            ) as progress:
                task = progress.add_task("[cyan]Authenticating...[/cyan]", total=None)
                
                response = self._make_request(
                    'POST',
                    '/api/login',
                    json={"username": username, "password": password}
                )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.user_data = data['user']
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                self._load_character()
                
                console.print(Panel.fit(
                    "[green]Authentication successful.[/green]\n"
                    f"Welcome back, Hunter {username}.",
                    title="System Access Granted",
                    border_style="green"
                ))
                
                self._show_character_info()
            else:
                console.print(Panel.fit(
                    f"[red]Authentication failed: {response.json().get('message', 'Unknown error')}[/red]",
                    title="Access Denied",
                    border_style="red"
                ))
        
        except Exception as e:
            console.print(Panel.fit(
                f"[red]Authentication error: {str(e)}[/red]",
                title="System Error",
                border_style="red"
            ))

    # ... [Rest of the client code remains the same but with updated styling] ...

def main():
    try:
        # Clear screen and show title
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(TITLE_ART)
        time.sleep(1)  # Dramatic pause
        
        # Initialize client
        client = TerminusaClient()
        client.cmdloop()
    except KeyboardInterrupt:
        console.print("\n[yellow]System shutdown initiated. Goodbye.[/yellow]")
    except Exception as e:
        console.print(Panel.fit(
            f"[red]Fatal system error: {str(e)}[/red]",
            title="Critical Error",
            border_style="red"
        ))
        sys.exit(1)

if __name__ == '__main__':
    main()
