# Read the current content of models/__init__.py
with open('models/__init__.py', 'r') as f:
    content = f.read()

# Replace the import statement
new_content = content.replace(
    """# Import Announcement after User to avoid circular imports
from .announcement import Announcement""",
    """# Avoid importing Announcement to avoid circular imports
# from .announcement import Announcement"""
)

# Write the modified content back to models/__init__.py
with open('models/__init__.py', 'w') as f:
    f.write(new_content)

print("Successfully modified models/__init__.py")
