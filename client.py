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
import time
import asyncio
from urllib.parse import urljoin
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()

class TerminusaClient(cmd.Cmd):
    intro = '''
╔════════════════════════════════════════════════════════╗
║                   Terminusa Online                     ║
║                     The Genesis                        ║
║                                                        ║
║              [cyan]Rise as a Hunter[/cyan]                      ║
║                                                        ║
║  Type [green]'help'[/green] for commands, [red]'quit'[/red] to exit        ║
╚════════════════════════════════════════════════════════╝
    '''
    prompt = '[bold blue]terminusa>[/bold blue] '
    
    def __init__(self):
        super().__init__()
        self.token = None
        self.user_data = None
        self.character = None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'TerminusaClient/1.0'})
        
        # Get server details from environment or use defaults
        self.base_url = os.getenv('API_URL', 'http://play.terminusa.online')
        
        # Test server connection
        self._test_server_connection()
        
    def _test_server_connection(self):
        """Test connection to the server"""
        try:
            with Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                transient=True,
            ) as progress:
                progress.add_task(description="Connecting to server...", total=None)
                response = self.session.get(urljoin(self.base_url, '/health'), timeout=5)
                
            if response.status_code == 200:
                console.print("[green]Successfully connected to server![/green]")
            else:
                console.print(f"[red]Server is not responding correctly (Status: {response.status_code})[/red]")
        except requests.exceptions.ConnectionError as e:
            console.print(f"[red]Could not connect to server at {self.base_url}[/red]")
            console.print("[yellow]Please ensure the server is running and the connection details are correct.[/yellow]")
            console.print(f"[dim]Error details: {str(e)}[/dim]")
        except Exception as e:
            console.print(f"[red]Error testing server connection: {str(e)}[/red]")

    def _make_request(self, method, endpoint, **kwargs):
        """Make a request to the server with proper error handling"""
        try:
            url = urljoin(self.base_url, endpoint)
            timeout = kwargs.pop('timeout', 10)
            
            # Add authorization header if token exists
            if self.token:
                kwargs.setdefault('headers', {})
                kwargs['headers']['Authorization'] = f'Bearer {self.token}'
            
            response = self.session.request(method, url, timeout=timeout, **kwargs)
            
            # Handle common status codes
            if response.status_code == 401:
                self.token = None
                self.user_data = None
                self.character = None
                raise Exception("Authentication failed. Please login again.")
            elif response.status_code == 403:
                raise Exception("Access denied. You don't have permission for this action.")
            elif response.status_code == 404:
                raise Exception("Resource not found.")
            elif response.status_code >= 500:
                raise Exception("Server error. Please try again later.")
            
            return response
        except requests.exceptions.ConnectionError:
            raise Exception(f"Connection error: Could not connect to server at {self.base_url}")
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Server is not responding.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
        
    def do_login(self, arg):
        """Login to your account"""
        username = Prompt.ask("[cyan]Username[/cyan]")
        password = getpass.getpass("[cyan]Password: [/cyan]")
        
        try:
            with Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                transient=True,
            ) as progress:
                progress.add_task(description="Logging in...", total=None)
                
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
                console.print("[green]Login successful![/green]")
                self._show_character_info()
            else:
                console.print(f"[red]Login failed: {response.json().get('message', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error during login: {str(e)}[/red]")

    def do_register(self, arg):
        """Create a new account"""
        username = Prompt.ask("[cyan]Username[/cyan]")
        email = Prompt.ask("[cyan]Email[/cyan]")
        password = getpass.getpass("[cyan]Password: [/cyan]")
        confirm_password = getpass.getpass("[cyan]Confirm Password: [/cyan]")
        
        if password != confirm_password:
            console.print("[red]Passwords do not match![/red]")
            return
        
        try:
            with Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                transient=True,
            ) as progress:
                progress.add_task(description="Creating account...", total=None)
                
                response = self._make_request(
                    'POST',
                    '/api/register',
                    json={
                        "username": username,
                        "email": email,
                        "password": password
                    }
                )
            
            if response.status_code in (200, 201):
                console.print("[green]Registration successful! Please check your email to verify your account.[/green]")
            else:
                console.print(f"[red]Registration failed: {response.json().get('message', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error during registration: {str(e)}[/red]")

    def do_status(self, arg):
        """Show your character status"""
        if not self._check_auth():
            return
        self._show_character_info()

    def do_inventory(self, arg):
        """Show your inventory"""
        if not self._check_auth():
            return
        
        try:
            with Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                transient=True,
            ) as progress:
                progress.add_task(description="Loading inventory...", total=None)
                response = self._make_request('GET', '/api/game/inventory')
            
            if response.status_code == 200:
                data = response.json()
                table = Table(title="[cyan]Inventory[/cyan]")
                table.add_column("Slot", style="cyan")
                table.add_column("Item", style="white")
                table.add_column("Quantity", style="green")
                table.add_column("Type", style="yellow")
                table.add_column("Rarity", style="magenta")
                
                for item in data['inventory']['items']:
                    table.add_row(
                        str(item['slot']),
                        item['name'],
                        str(item['quantity']),
                        item['type'],
                        self._get_rarity_color(item['rarity'])
                    )
                
                console.print(table)
            else:
                console.print("[red]Failed to fetch inventory[/red]")
        
        except Exception as e:
            console.print(f"[red]Error fetching inventory: {str(e)}[/red]")

    def do_gates(self, arg):
        """List available gates"""
        if not self._check_auth():
            return
        
        try:
            with Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                transient=True,
            ) as progress:
                progress.add_task(description="Loading gates...", total=None)
                response = self._make_request('GET', '/api/game/gates')
            
            if response.status_code == 200:
                data = response.json()
                table = Table(title="[cyan]Available Gates[/cyan]")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="white")
                table.add_column("Type", style="yellow")
                table.add_column("Level Req", style="red")
                table.add_column("Rank Req", style="magenta")
                table.add_column("Players", style="green")
                
                for gate in data['gates']:
                    table.add_row(
                        str(gate['id']),
                        gate['name'],
                        gate['type'],
                        str(gate['level_requirement']),
                        gate['rank_requirement'],
                        f"{gate['min_players']}-{gate['max_players']}"
                    )
                
                console.print(table)
            else:
                console.print("[red]Failed to fetch gates[/red]")
        
        except Exception as e:
            console.print(f"[red]Error fetching gates: {str(e)}[/red]")

    def do_enter(self, arg):
        """Enter a gate (usage: enter <gate_id>)"""
        if not self._check_auth():
            return
            
        if not arg:
            console.print("[red]Please specify a gate ID[/red]")
            return
            
        try:
            gate_id = int(arg)
            with Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                transient=True,
            ) as progress:
                progress.add_task(description="Entering gate...", total=None)
                response = self._make_request(
                    'POST',
                    f'/api/game/gates/{gate_id}/enter'
                )
            
            if response.status_code == 200:
                data = response.json()
                self._handle_gate_session(data['session_id'])
            else:
                console.print(f"[red]Failed to enter gate: {response.json().get('message', 'Unknown error')}[/red]")
        
        except ValueError:
            console.print("[red]Invalid gate ID[/red]")
        except Exception as e:
            console.print(f"[red]Error entering gate: {str(e)}[/red]")

    def do_quit(self, arg):
        """Exit the game"""
        console.print("[yellow]Thanks for playing! See you next time.[/yellow]")
        return True

    def _check_auth(self):
        """Check if user is authenticated"""
        if not self.token:
            console.print("[red]You must be logged in to use this command[/red]")
            return False
        return True

    def _load_character(self):
        """Load character data"""
        try:
            with Progress(
                SpinnerColumn(),
                "[progress.description]{task.description}",
                transient=True,
            ) as progress:
                progress.add_task(description="Loading character...", total=None)
                response = self._make_request('GET', '/api/game/profile')
            
            if response.status_code == 200:
                self.character = response.json()['character']
        except Exception as e:
            console.print(f"[red]Error loading character: {str(e)}[/red]")

    def _show_character_info(self):
        """Display character information"""
        if not self.character:
            console.print("[red]Character data not available[/red]")
            return
            
        char = self.character
        
        # Basic Info
        console.print(Panel(f"""
[bold cyan]Name:[/bold cyan] {self.user_data['username']}
[bold cyan]Level:[/bold cyan] {char['level']} ([cyan]{char['experience']}/1000 XP[/cyan])
[bold cyan]Rank:[/bold cyan] [{self._get_rank_color(char['rank'])}]{char['rank']}[/{self._get_rank_color(char['rank'])}]
[bold cyan]Title:[/bold cyan] {char['title'] or 'None'}
        """, title="[bold cyan]Character Info[/bold cyan]"))
        
        # Stats
        stats_table = Table(title="[cyan]Stats[/cyan]")
        stats_table.add_column("Base Stats", justify="right", style="cyan")
        stats_table.add_column("Value", justify="left", style="green")
        stats_table.add_column("Combat Stats", justify="right", style="cyan")
        stats_table.add_column("Value", justify="left", style="green")
        
        stats_table.add_row(
            "Strength", str(char['strength']),
            "Physical Attack", str(char['physical_attack'])
        )
        stats_table.add_row(
            "Agility", str(char['agility']),
            "Magical Attack", str(char['magical_attack'])
        )
        stats_table.add_row(
            "Intelligence", str(char['intelligence']),
            "Physical Defense", str(char['physical_defense'])
        )
        stats_table.add_row(
            "Vitality", str(char['vitality']),
            "Magical Defense", str(char['magical_defense'])
        )
        stats_table.add_row(
            "Wisdom", str(char['wisdom']),
            "Critical Chance", f"{char['critical_chance']}%"
        )
        
        console.print(stats_table)
        
        # Progress
        progress_table = Table(title="[cyan]Progress[/cyan]")
        progress_table.add_column("Achievement", justify="right", style="cyan")
        progress_table.add_column("Count", justify="left", style="green")
        
        progress_table.add_row("Gates Cleared", str(char['gates_cleared']))
        progress_table.add_row("Bosses Defeated", str(char['bosses_defeated']))
        progress_table.add_row("Quests Completed", str(char['quests_completed']))
        
        console.print(progress_table)

    async def _handle_gate_session(self, session_id):
        """Handle gate combat session"""
        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]Exploring gate...", total=100)
                
                while not progress.finished:
                    response = self._make_request(
                        'GET',
                        f'/api/game/gates/session/{session_id}'
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data['status'] == 'completed':
                            self._show_gate_results(data['results'])
                            break
                        elif data['status'] == 'failed':
                            console.print("[red]Gate exploration failed![/red]")
                            break
                        else:
                            progress.update(task, advance=10)
                            await asyncio.sleep(1)
                    else:
                        console.print("[red]Failed to get gate session status[/red]")
                        break
        
        except Exception as e:
            console.print(f"[red]Error in gate session: {str(e)}[/red]")

    def _show_gate_results(self, results):
        """Display gate exploration results"""
        console.print(Panel(f"""
[green]Gate Cleared Successfully![/green]

[bold cyan]Experience Gained:[/bold cyan] {results['experience']}
[bold cyan]Items Found:[/bold cyan] {len(results['items'])}
[bold cyan]Crystals Found:[/bold cyan] {results['crystals']}
        """, title="[cyan]Results[/cyan]"))
        
        if results['items']:
            items_table = Table(title="[cyan]Items Found[/cyan]")
            items_table.add_column("Item", style="white")
            items_table.add_column("Type", style="yellow")
            items_table.add_column("Rarity", style="magenta")
            
            for item in results['items']:
                items_table.add_row(
                    item['name'],
                    item['type'],
                    self._get_rarity_color(item['rarity'])
                )
            
            console.print(items_table)

    @staticmethod
    def _get_rarity_color(rarity):
        colors = {
            'common': 'white',
            'uncommon': 'green',
            'rare': 'blue',
            'epic': 'magenta',
            'legendary': 'yellow',
            'mythic': 'red',
            'divine': 'cyan'
        }
        return f"[{colors.get(rarity.lower(), 'white')}]{rarity}[/{colors.get(rarity.lower(), 'white')}]"

    @staticmethod
    def _get_rank_color(rank):
        colors = {
            'F': 'white',
            'E': 'green',
            'D': 'blue',
            'C': 'magenta',
            'B': 'yellow',
            'A': 'red',
            'S': 'cyan'
        }
        return colors.get(rank, 'white')

def main():
    try:
        client = TerminusaClient()
        client.cmdloop()
    except KeyboardInterrupt:
        console.print("\n[yellow]Thanks for playing! See you next time.[/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    main()
