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
        
        # Create tables in specific order with explicit checks
        from sqlalchemy import inspect
        
        # Create users table first
        User.__table__.create(db.engine)
        if not inspect(db.engine).has_table('users'):
            raise Exception("Failed to create users table")
        
        # Create remaining tables
        tables = [
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
        
        # Create tables with foreign key constraints
        for table in tables:
            table.create(bind=db.engine)
        
        # Verify all tables were created
        inspector = inspect(db.engine)
        required_tables = ['users', 'wallets', 'announcements', 'guilds', 
                          'parties', 'gates', 'magic_beasts', 'inventory_items',
                          'items', 'mounts', 'pets', 'skills', 'quests',
                          'guild_quests', 'achievements', 'transactions']
        
        for table_name in required_tables:
            if not inspector.has_table(table_name):
                raise Exception(f"Failed to create table: {table_name}")

        
        print("[INFO] Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
