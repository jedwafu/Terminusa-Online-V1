# Read the current content of models/__init__.py
with open('models/__init__.py', 'r') as f:
    content = f.read()

# Replace the import order and add a function to initialize the models
new_content = content.replace(
    "# Import all models",
    """# Import all models
# Import User first to avoid circular imports
from .user import User"""
)

new_content = new_content.replace(
    "from .user import User",
    ""
)

new_content = new_content.replace(
    "from .announcement import Announcement",
    """# Import Announcement after User to avoid circular imports
from .announcement import Announcement"""
)

# Write the modified content back to models/__init__.py
with open('models/__init__.py', 'w') as f:
    f.write(new_content)

print("Successfully modified models/__init__.py")
