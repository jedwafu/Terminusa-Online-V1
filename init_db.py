from web_app import create_app
from models import db

def initialize_database():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create tables in specific order to handle dependencies
        from models import (
            User, 
            Wallet,
            Announcement,
            Guild,
            Party,
            Gate,
            MagicBeast,
            InventoryItem,
            Item,
            Mount,
            Pet,
            Skill,
            Quest,
            GuildQuest,
            Achievement,
            Transaction
        )
        
        # Create tables without foreign keys first
        User.__table__.create(db.engine)
        
        # Create tables with foreign keys
        Wallet.__table__.create(db.engine)
        Announcement.__table__.create(db.engine)
        Guild.__table__.create(db.engine)
        Party.__table__.create(db.engine)
        Gate.__table__.create(db.engine)
        MagicBeast.__table__.create(db.engine)
        InventoryItem.__table__.create(db.engine)
        Item.__table__.create(db.engine)
        Mount.__table__.create(db.engine)
        Pet.__table__.create(db.engine)
        Skill.__table__.create(db.engine)
        Quest.__table__.create(db.engine)
        GuildQuest.__table__.create(db.engine)
        Achievement.__table__.create(db.engine)
        Transaction.__table__.create(db.engine)
        
        print("[INFO] Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
