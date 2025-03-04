# Read the current content of web_app.py
with open('web_app.py', 'r') as f:
    content = f.read()

# Replace the import statement
new_content = content.replace(
    "from models import User, PlayerCharacter, Wallet, Inventory, Transaction, Gate, Guild, Item, Announcement",
    """# Import models individually to avoid circular imports
from models.user import User
from models.player import PlayerCharacter
from models.wallet import Wallet
from models.inventory import Inventory
from models.transaction import Transaction
from models.gate import Gate
from models.guild import Guild
from models.item import Item
# Import Announcement last to avoid circular imports
from models.announcement import Announcement"""
)

# Write the modified content back to web_app.py
with open('web_app.py', 'w') as f:
    f.write(new_content)

print("Successfully modified web_app.py")
