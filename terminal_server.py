import asyncio
import websockets
import json
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
import jwt
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, InventoryItem

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

# Database setup
engine = create_engine(os.getenv('DATABASE_URL'))
Session = sessionmaker(bind=engine)

class TerminalSession:
    def __init__(self, websocket, user):
        self.websocket = websocket
        self.user = user
        self.current_location = "hub"
        self.in_dungeon = False
        self.dungeon_level = 0

    async def send_message(self, message, color="white"):
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

    async def handle_command(self, command):
        cmd_parts = command.strip().lower().split()
        if not cmd_parts:
            return

        cmd = cmd_parts[0]
        args = cmd_parts[1:]

        try:
            if cmd == "help":
                await self.cmd_help()
            elif cmd == "status":
                await self.cmd_status()
            elif cmd == "inventory":
                await self.cmd_inventory()
            elif cmd == "explore":
                await self.cmd_explore()
            elif cmd == "enter":
                await self.cmd_enter_dungeon(args)
            elif cmd == "attack":
                await self.cmd_attack()
            elif cmd == "flee":
                await self.cmd_flee()
            elif cmd == "market":
                await self.cmd_market()
            elif cmd == "balance":
                await self.cmd_balance()
            else:
                await self.send_message(f"Unknown command: {cmd}. Type 'help' for available commands.", "red")
        except Exception as e:
            logger.error(f"Error handling command {cmd}: {str(e)}")
            await self.send_message("An error occurred while processing your command.", "red")

    async def cmd_help(self):
        help_text = """
Available Commands:
  help        - Show this help message
  status      - Show your hunter status
  inventory   - Show your inventory
  explore     - Look for dungeons
  enter [lvl] - Enter a dungeon of specified level
  attack      - Attack monsters in dungeon
  flee        - Escape from dungeon
  market      - Access the marketplace
  balance     - Check your crystal and Exon balance
"""
        await self.send_message(help_text, "cyan")

    async def cmd_status(self):
        session = Session()
        user = session.query(User).get(self.user.id)
        status_text = f"""
Hunter Status:
  Name: {user.username}
  Level: {user.hunter_level}
  Class: {user.hunter_class or 'Unassigned'}
  Location: {self.current_location.title()}
  Crystals: {user.crystals}
  Exons Balance: {user.exons_balance:.2f}
"""
        session.close()
        await self.send_message(status_text, "green")

    async def cmd_inventory(self):
        session = Session()
        items = session.query(InventoryItem).filter_by(user_id=self.user.id).all()
        if not items:
            await self.send_message("Your inventory is empty.", "yellow")
        else:
            inventory_text = "\nInventory:\n"
            for item in items:
                inventory_text += f"  {item.name} (x{item.quantity}) - {item.description}\n"
        session.close()
        await self.send_message(inventory_text, "cyan")

    async def cmd_explore(self):
        if self.in_dungeon:
            await self.send_message("You are already in a dungeon!", "red")
            return

        await self.send_message("Searching for dungeons...", "yellow")
        await asyncio.sleep(2)  # Simulated search delay
        
        dungeons = [
            {"level": 1, "difficulty": "Easy"},
            {"level": 3, "difficulty": "Medium"},
            {"level": 5, "difficulty": "Hard"}
        ]
        
        result = "\nAvailable Dungeons:\n"
        for dungeon in dungeons:
            result += f"  Level {dungeon['level']} Dungeon - {dungeon['difficulty']}\n"
        result += "\nUse 'enter [level]' to enter a dungeon."
        
        await self.send_message(result, "green")

    async def cmd_enter_dungeon(self, args):
        if self.in_dungeon:
            await self.send_message("You are already in a dungeon!", "red")
            return

        if not args:
            await self.send_message("Please specify a dungeon level: 'enter [level]'", "red")
            return

        try:
            level = int(args[0])
            if level < 1:
                await self.send_message("Invalid dungeon level.", "red")
                return

            session = Session()
            user = session.query(User).get(self.user.id)
            if level > user.hunter_level + 2:
                await self.send_message("This dungeon is too dangerous for your current level!", "red")
                session.close()
                return

            self.in_dungeon = True
            self.dungeon_level = level
            self.current_location = f"dungeon_level_{level}"
            
            await self.send_message(f"Entering level {level} dungeon...", "yellow")
            await asyncio.sleep(1)
            await self.send_message("You are now in the dungeon. Use 'attack' to fight monsters or 'flee' to escape.", "green")
            
            session.close()
        except ValueError:
            await self.send_message("Invalid dungeon level.", "red")

    async def cmd_attack(self):
        if not self.in_dungeon:
            await self.send_message("You must be in a dungeon to attack!", "red")
            return

        # Simulate combat
        await self.send_message("Engaging in combat...", "yellow")
        await asyncio.sleep(1)

        # Random outcome
        import random
        success = random.random() > 0.3

        session = Session()
        user = session.query(User).get(self.user.id)

        if success:
            crystals_gained = random.randint(1, 5) * self.dungeon_level
            user.crystals += crystals_gained
            await self.send_message(f"Victory! You gained {crystals_gained} crystals!", "green")

            # Chance for item drop
            if random.random() < 0.3:
                item_name = random.choice(["Health Potion", "Mana Crystal", "Ancient Relic"])
                new_item = InventoryItem(
                    user_id=user.id,
                    item_type="loot",
                    name=item_name,
                    description=f"Found in level {self.dungeon_level} dungeon",
                    quantity=1
                )
                session.add(new_item)
                await self.send_message(f"You found a {item_name}!", "cyan")
        else:
            await self.send_message("You were defeated! Consider fleeing or trying again.", "red")

        session.commit()
        session.close()

    async def cmd_flee(self):
        if not self.in_dungeon:
            await self.send_message("You're not in a dungeon!", "red")
            return

        await self.send_message("Attempting to flee...", "yellow")
        await asyncio.sleep(1)

        self.in_dungeon = False
        self.dungeon_level = 0
        self.current_location = "hub"
        await self.send_message("You successfully escaped from the dungeon!", "green")

    async def cmd_market(self):
        if self.in_dungeon:
            await self.send_message("You cannot access the market while in a dungeon!", "red")
            return

        # TODO: Implement marketplace functionality
        await self.send_message("Market functionality coming soon!", "yellow")

    async def cmd_balance(self):
        session = Session()
        user = session.query(User).get(self.user.id)
        balance_text = f"""
Currency Balance:
  Crystals: {user.crystals}
  Exons: {user.exons_balance:.2f}
"""
        session.close()
        await self.send_message(balance_text, "green")

async def authenticate_token(token):
    try:
        payload = jwt.decode(
            token,
            os.getenv('JWT_SECRET_KEY'),
            algorithms=['HS256']
        )
        session = Session()
        user = session.query(User).get(payload['user_id'])
        session.close()
        return user
    except:
        return None

async def terminal_server(websocket, path):
    try:
        # Authenticate user
        auth_message = await websocket.recv()
        auth_data = json.loads(auth_message)
        user = await authenticate_token(auth_data.get('token'))
        
        if not user:
            await websocket.send("Authentication failed")
            return

        # Create terminal session
        session = TerminalSession(websocket, user)
        await session.send_message(f"Welcome to Terminusa Online, {user.username}!", "green")
        await session.send_message("Type 'help' for available commands.\n", "cyan")

        # Handle commands
        async for message in websocket:
            await session.handle_command(message)

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected")
    except Exception as e:
        logger.error(f"Error in terminal server: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv('TERMINAL_PORT', 6789))
    start_server = websockets.serve(
        terminal_server,
        "0.0.0.0",
        port,
        ping_interval=None
    )

    logger.info(f"Terminal server starting on port {port}")
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
