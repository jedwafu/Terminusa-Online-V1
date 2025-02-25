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
        
        # Create tables without foreign key constraints first
        tables = [
            User.__table__,
            Wallet.__table__,
            Announcement.__table__,
            Guild.__table__,
            Party.__table__,
            Gate.__table__,
            MagicBeast.__table__,
            InventoryItem.__table__,
            Item.__table__,
            Mount.__table__,
            Pet.__table__,
            Skill.__table__,
            Quest.__table__,
            GuildQuest.__table__,
            Achievement.__table__,
            Transaction.__table__
        ]
        
        # Create tables without foreign key constraints
        for table in tables:
            table.create(bind=db.engine, checkfirst=False)
        
        # Add foreign key constraints after all tables exist
        from sqlalchemy import DDL
        db.engine.execute(DDL(
            "ALTER TABLE wallets ADD CONSTRAINT fk_wallets_users "
            "FOREIGN KEY (user_id) REFERENCES users (id)"
        ))
        
        print("[INFO] Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
