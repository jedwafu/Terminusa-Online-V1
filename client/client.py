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
from rich.progress import Progress
import time
import asyncio

console = Console()

class TerminusaClient(cmd.Cmd):
    intro = '''
╔════════════════════════════════════════════════════════╗
║                   Terminusa Online                     ║
║                     The Genesis                        ║
║                                                        ║
║  Type 'help' for commands, 'quit' or Ctrl+D to exit    ║
╚════════════════════════════════════════════════════════╝
    '''
    prompt = '[bold blue]terminusa>[/bold blue] '
    
    def __init__(self):
        super().__init__()
        self.token = None
        self.user_data = None
        self.character = None
        self.base_url = os.getenv('API_URL', 'http://localhost:5000')
        
    def do_login(self, arg):
        """Login to your account"""
        username = Prompt.ask("Username")
        password = getpass.getpass("Password: ")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['token']
                self.user_data = data['user']
                self._load_character()
                console.print("[green]Login successful![/green]")
                self._show_character_info()
            else:
                console.print(f"[red]Login failed: {response.json().get('message', 'Unknown error')}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error during login: {str(e)}[/red]")

    def do_register(self, arg):
        """Create a new account"""
        username = Prompt.ask("Username")
        email = Prompt.ask("Email")
        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm Password: ")
        
        if password != confirm_password:
            console.print("[red]Passwords do not match![/red]")
            return
        
        try:
            response = requests.post(
                f"{self.base_url}/api/register",
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
            response = requests.get(
                f"{self.base_url}/api/game/inventory",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                table = Table(title="Inventory")
                table.add_column("Slot")
                table.add_column("Item")
                table.add_column("Quantity")
                table.add_column("Type")
                table.add_column("Rarity")
                
                for item in data['inventory']['items']:
                    table.add_row(
                        str(item['slot']),
                        item['name'],
                        str(item['quantity']),
                        item['type'],
                        f"[{self._get_rarity_color(item['rarity'])}]{item['rarity']}[/{self._get_rarity_color(item['rarity'])}]"
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
            response = requests.get(
                f"{self.base_url}/api/game/gates",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                table = Table(title="Available Gates")
                table.add_column("ID")
                table.add_column("Name")
                table.add_column("Type")
                table.add_column("Level Req")
                table.add_column("Rank Req")
                table.add_column("Players")
                
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
            response = requests.post(
                f"{self.base_url}/api/game/gates/{gate_id}/enter",
                headers=self._get_headers()
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

    def _get_headers(self):
        """Get headers for API requests"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def _load_character(self):
        """Load character data"""
        try:
            response = requests.get(
                f"{self.base_url}/api/game/profile",
                headers=self._get_headers()
            )
            
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
[bold]Name:[/bold] {self.user_data['username']}
[bold]Level:[/bold] {char['level']} ([cyan]{char['experience']}/1000 XP[/cyan])
[bold]Rank:[/bold] [{self._get_rank_color(char['rank'])}]{char['rank']}[/{self._get_rank_color(char['rank'])}]
[bold]Title:[/bold] {char['title'] or 'None'}
        """, title="Character Info"))
        
        # Stats
        stats_table = Table(title="Stats")
        stats_table.add_column("Base Stats", justify="right")
        stats_table.add_column("Value", justify="left")
        stats_table.add_column("Combat Stats", justify="right")
        stats_table.add_column("Value", justify="left")
        
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
        progress_table = Table(title="Progress")
        progress_table.add_column("Achievement", justify="right")
        progress_table.add_column("Count", justify="left")
        
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
                    response = requests.get(
                        f"{self.base_url}/api/game/gates/session/{session_id}",
                        headers=self._get_headers()
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

[bold]Experience Gained:[/bold] {results['experience']}
[bold]Items Found:[/bold] {len(results['items'])}
[bold]Crystals Found:[/bold] {results['crystals']}
        """, title="Results"))
        
        if results['items']:
            items_table = Table(title="Items Found")
            items_table.add_column("Item")
            items_table.add_column("Type")
            items_table.add_column("Rarity")
            
            for item in results['items']:
                items_table.add_row(
                    item['name'],
                    item['type'],
                    f"[{self._get_rarity_color(item['rarity'])}]{item['rarity']}[/{self._get_rarity_color(item['rarity'])}]"
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
        return colors.get(rarity.lower(), 'white')

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
