import os

# Read the current content of models/__init__.py
with open('models/__init__.py', 'r') as f:
    content = f.read()

# Replace the import order
new_content = content.replace(
    "from .user import User",
    "# Import User first to avoid circular imports\nfrom .user import User"
)

new_content = new_content.replace(
    "from .announcement import Announcement",
    "# Import Announcement after User\nfrom .announcement import Announcement"
)

# Write the modified content back to models/__init__.py
with open('models/__init__.py', 'w') as f:
    f.write(new_content)

print("Successfully modified models/__init__.py")
