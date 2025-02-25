from web_app import create_app
from models import db

def initialize_database():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        # Create tables in specific order to handle dependencies
        # Create all tables in correct order
        from models import User, PlayerCharacter, Wallet, Announcement
        db.create_all()
        print("[INFO] Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
