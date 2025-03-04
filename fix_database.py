# Read the current content of database.py
with open('database.py', 'r') as f:
    content = f.read()

# Replace the init_db function
new_content = content.replace(
    """def init_db(app):
    \"\"\"Initialize the database\"\"\"
    db.init_app(app)
    with app.app_context():
        # Import all models to ensure they're registered
        from models.user import User
        from models.player import PlayerCharacter
        from models import Wallet
        from models.announcement import Announcement
        
        # Let SQLAlchemy create all tables in the correct order
        db.create_all()""",
    """def init_db(app):
    \"\"\"Initialize the database\"\"\"
    db.init_app(app)
    with app.app_context():
        # Import all models to ensure they're registered
        from models.user import User
        from models.player import PlayerCharacter
        from models import Wallet
        # Avoid importing Announcement to avoid circular imports
        
        # Let SQLAlchemy create all tables in the correct order
        db.create_all()"""
)

# Write the modified content back to database.py
with open('database.py', 'w') as f:
    f.write(new_content)

print("Successfully modified database.py")
