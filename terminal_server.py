"""
Terminal Server for Terminusa Online using xterm.js
"""
import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Set
import websockets
from websockets.server import WebSocketServerProtocol
from game_manager import GameManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/terminal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TerminalServer:
    """Terminal server using WebSocket for xterm.js communication"""
    
    def __init__(self):
        self.game_manager = GameManager()
        self.active_sessions: Dict[str, WebSocketServerProtocol] = {}
        self.user_sessions: Dict[int, str] = {}  # user_id -> session_id
        
        # Available commands
        self.commands = {
            'help': self.cmd_help,
            'login': self.cmd_login,
            'logout': self.cmd_logout,
            'gate': self.cmd_gate,
            'party': self.cmd_party,
            'guild': self.cmd_guild,
            'inventory': self.cmd_inventory,
            'equip': self.cmd_equip,
            'unequip': self.cmd_unequip,
            'stats': self.cmd_stats,
            'shop': self.cmd_shop,
            'buy': self.cmd_buy,
            'sell': self.cmd_sell,
            'trade': self.cmd_trade,
            'gamble': self.cmd_gamble,
            'gacha': self.cmd_gacha,
            'job': self.cmd_job,
            'skills': self.cmd_skills,
            'achievements': self.cmd_achievements,
            'mount': self.cmd_mount,
            'pet': self.cmd_pet,
            'clear': self.cmd_clear
        }

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        session_id = os.urandom(16).hex()
        self.active_sessions[session_id] = websocket
        
        try:
            # Send welcome message
            await self.send_welcome_message(websocket)
            
            # Handle messages
            async for message in websocket:
                try:
                    await self.handle_message(session_id, message)
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")
                    await self.send_error(websocket, str(e))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {session_id}")
        finally:
            # Cleanup
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            # Remove user session if exists
            for user_id, sess_id in list(self.user_sessions.items()):
                if sess_id == session_id:
                    del self.user_sessions[user_id]

    async def handle_message(self, session_id: str, message: str):
        """Handle incoming message from terminal"""
        websocket = self.active_sessions[session_id]
        
        # Parse command
        parts = message.strip().split()
        if not parts:
            return
            
        command = parts[0].lower()
        args = parts[1:]
        
        # Execute command if available
        if command in self.commands:
            await self.commands[command](websocket, args)
        else:
            await self.send_error(websocket, f"Unknown command: {command}")

    async def send_welcome_message(self, websocket: WebSocketServerProtocol):
        """Send welcome message to new connection"""
        welcome = """
╔════════════════════════════════════════════════════════════════╗
║                    Welcome to Terminusa Online                  ║
║                                                                ║
║  Type 'help' for a list of commands                           ║
║  Login with: login <username> <password>                       ║
║                                                                ║
║  A Terminal-based MMORPG inspired by Solo Leveling            ║
╚════════════════════════════════════════════════════════════════╝
"""
        await websocket.send(json.dumps({
            "type": "output",
            "content": welcome
        }))

    async def cmd_help(self, websocket: WebSocketServerProtocol, args: list):
        """Show help message"""
        help_text = """
Available Commands:
------------------
General:
  help                 Show this help message
  login <user> <pass>  Login to your account
  logout              Logout from current session
  clear               Clear terminal screen

Character:
  stats               Show character stats
  inventory           Show inventory
  equip <item_id>     Equip an item
  unequip <item_id>   Unequip an item
  skills              Show available skills
  job                Show job information
  achievements        Show achievements

Combat:
  gate list          List available gates
  gate enter <id>    Enter a gate
  gate leave         Leave current gate
  gate status        Show current gate status

Party:
  party create       Create a new party
  party join <id>    Join a party
  party leave        Leave current party
  party list         List party members

Guild:
  guild info         Show guild information
  guild join <id>    Join a guild
  guild leave        Leave current guild
  guild bank         Show guild bank

Economy:
  shop               Show hunter shop
  buy <item> <qty>   Buy from shop
  sell <item> <qty>  Sell to shop
  trade <user> <item> <qty> <price>  Trade with user
  gamble flip <amount>  Play coin flip
  gacha mount        Summon mount
  gacha pet          Summon pet

Mounts & Pets:
  mount list         List your mounts
  mount summon <id>  Summon a mount
  pet list          List your pets
  pet summon <id>   Summon a pet
"""
        await websocket.send(json.dumps({
            "type": "output",
            "content": help_text
        }))

    async def send_error(self, websocket: WebSocketServerProtocol, message: str):
        """Send error message"""
        await websocket.send(json.dumps({
            "type": "error",
            "content": f"Error: {message}"
        }))

    async def send_success(self, websocket: WebSocketServerProtocol, message: str):
        """Send success message"""
        await websocket.send(json.dumps({
            "type": "success",
            "content": message
        }))

    # Implement other command handlers...
    # Each command handler should:
    # 1. Validate input
    # 2. Process through game_manager
    # 3. Format and send response
    # 4. Handle errors appropriately

async def main():
    """Start terminal server"""
    try:
        terminal_server = TerminalServer()
        
        server = await websockets.serve(
            terminal_server.handle_connection,
            "0.0.0.0",
            6789,
            ping_interval=30,
            ping_timeout=10
        )
        
        logger.info("Terminal server started on ws://0.0.0.0:6789")
        
        await server.wait_closed()
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
