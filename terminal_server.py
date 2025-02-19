import asyncio
import websockets
import json
import jwt
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

from models import db, User
from terminal_commands import TerminalCommands
from game_handler import GameHandler

# Load environment variables
load_dotenv()

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger('terminal_server')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'logs/terminal.log',
    maxBytes=1024 * 1024,
    backupCount=10
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'
))
logger.addHandler(handler)

# Initialize handlers
terminal_commands = TerminalCommands()
game_handler = GameHandler()

# Active sessions
active_sessions = {}

class TerminalSession:
    def __init__(self, websocket, user):
        self.websocket = websocket
        self.user = user
        self.command_history = []
        self.last_command_time = datetime.utcnow()

    async def send_message(self, message, color="white"):
        """Send formatted message to terminal"""
        colors = {
            "red": "\x1b[31m",
            "green": "\x1b[32m",
            "yellow": "\x1b[33m",
            "blue": "\x1b[34m",
            "magenta": "\x1b[35m",
            "cyan": "\x1b[36m",
            "white": "\x1b[37m"
        }
        reset = "\x1b[0m"
        await self.websocket.send(f"{colors.get(color, '')}{message}{reset}")

    async def handle_command(self, command_text):
        """Handle terminal command"""
        # Split command and args
        parts = command_text.strip().split()
        if not parts:
            return
            
        command = parts[0].lower()
        args = parts[1:]
        
        # Add to command history
        self.command_history.append(command_text)
        self.last_command_time = datetime.utcnow()
        
        try:
            # Process command
            result = terminal_commands.handle_command(self.user, command, args)
            
            # Send response
            if result['success']:
                await self.send_message(result['message'], "green")
            else:
                await self.send_message(result['message'], "red")
                
            # Handle special commands
            if command == 'enter' and result['success']:
                await self.start_combat_session(result['session_id'])
                
        except Exception as e:
            logger.error(f"Error handling command '{command}': {str(e)}")
            await self.send_message(
                "An error occurred while processing your command.",
                "red"
            )

    async def start_combat_session(self, session_id):
        """Start combat session in gate"""
        try:
            await self.send_message("\nEntering gate...", "yellow")
            
            while True:
                # Process combat round
                result = game_handler.process_combat(session_id)
                if not result['success']:
                    await self.send_message(result['message'], "red")
                    break
                    
                # Display combat messages
                for msg in result['messages']:
                    await self.send_message(msg)
                    await asyncio.sleep(0.5)  # Add delay between messages
                    
                # Check if combat ended
                if 'gate_cleared' in result and result['gate_cleared']:
                    if 'drops' in result:
                        await self.send_message("\nObtained items:", "green")
                        for drop in result['drops']:
                            if drop['type'] == 'item':
                                await self.send_message(
                                    f"- {drop['item'].name}",
                                    "cyan"
                                )
                            elif drop['type'] == 'crystal':
                                await self.send_message(
                                    f"- {drop['amount']} Crystals",
                                    "yellow"
                                )
                    break
                elif self.user.hp <= 0:
                    await self.send_message("\nYou have died!", "red")
                    break
                    
                await asyncio.sleep(1)  # Combat round delay
                
        except Exception as e:
            logger.error(f"Error in combat session: {str(e)}")
            await self.send_message(
                "An error occurred during combat.",
                "red"
            )

async def authenticate_token(token):
    """Authenticate JWT token"""
    try:
        payload = jwt.decode(
            token,
            os.getenv('JWT_SECRET_KEY'),
            algorithms=['HS256']
        )
        user = User.query.get(payload['user_id'])
        return user
    except:
        return None

async def terminal_handler(websocket, path):
    """Handle terminal WebSocket connection"""
    try:
        # Wait for authentication
        auth_message = await websocket.recv()
        auth_data = json.loads(auth_message)
        user = await authenticate_token(auth_data.get('token'))
        
        if not user:
            await websocket.send("Authentication failed")
            return

        # Create terminal session
        session = TerminalSession(websocket, user)
        active_sessions[user.id] = session
        
        # Send welcome message
        await session.send_message(
            f"Welcome to Terminusa Online, {user.username}!",
            "green"
        )
        await session.send_message(
            "Type 'help' for available commands.\n",
            "cyan"
        )

        # Handle commands
        async for message in websocket:
            await session.handle_command(message)

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected")
    except Exception as e:
        logger.error(f"Error in terminal handler: {str(e)}")
    finally:
        # Cleanup session
        if user and user.id in active_sessions:
            del active_sessions[user.id]

if __name__ == "__main__":
    port = int(os.getenv('TERMINAL_PORT', 6789))
    start_server = websockets.serve(
        terminal_handler,
        "0.0.0.0",
        port,
        ping_interval=None
    )

    logger.info(f"Terminal server starting on port {port}")
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
