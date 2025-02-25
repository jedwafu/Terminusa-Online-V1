from web_app import create_app
from models import db

def initialize_database():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        # Create tables in specific order to handle dependencies
        # Drop all existing tables and create new ones in correct order
        from models import User, PlayerCharacter, Wallet, Announcement
        db.drop_all()
        
        # Create tables in specific order to handle dependencies
        User.__table__.create(db.engine)
        PlayerCharacter.__table__.create(db.engine)
        Wallet.__table__.create(db.engine)
        Announcement.__table__.create(db.engine)
        print("[INFO] Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
