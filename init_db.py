from web_app import create_app
from models import db

def initialize_database():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        # Create tables in specific order to handle dependencies
        # Drop all existing tables
        db.drop_all()
        
        # Create tables without foreign keys first
        from models import User, PlayerCharacter, Announcement
        User.__table__.create(db.engine)
        PlayerCharacter.__table__.create(db.engine)
        Announcement.__table__.create(db.engine)
        
        # Create tables with foreign keys
        from models import Wallet
        Wallet.__table__.create(db.engine)
        
        # Add foreign key constraints
        from sqlalchemy import DDL
        db.engine.execute(DDL(
            "ALTER TABLE wallets ADD CONSTRAINT fk_wallets_users "
            "FOREIGN KEY (user_id) REFERENCES users (id)"
        ))
        print("[INFO] Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
