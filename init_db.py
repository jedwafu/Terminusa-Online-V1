import logging
import os
from web_app import create_app
from models import db

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/db_init.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the database"""
    logger.info("Starting database initialization")
    app = create_app()
    with app.app_context():
        logger.info("App context created")
        # Drop all existing tables
        logger.info("Dropping all existing tables")
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
        logger.info("Creating users table")
        User.__table__.create(db.engine)
        if not inspect(db.engine).has_table('users'):
            logger.error("Failed to create users table")
            raise Exception("Failed to create users table")
            
        # Create wallets table without foreign key first
        logger.info("Creating wallets table without foreign key")
        Wallet.__table__.create(db.engine, checkfirst=False)
        if not inspect(db.engine).has_table('wallets'):
            logger.error("Failed to create wallets table")
            raise Exception("Failed to create wallets table")
            
        # Add foreign key constraints after both tables exist
        logger.info("Adding foreign key constraints")
        from sqlalchemy import DDL
        try:
            db.engine.execute(DDL(
                "ALTER TABLE wallets ADD CONSTRAINT fk_wallets_users "
                "FOREIGN KEY (user_id) REFERENCES users(id)"
            ))
            logger.info("Foreign key constraint added successfully")
        except Exception as e:
            logger.error(f"Failed to add foreign key constraint: {str(e)}")
            raise Exception(f"Failed to add foreign key constraint: {str(e)}")
            
        # Create tables in dependency order
        logger.info("Creating remaining tables")
        
        # Create base tables first
        logger.info("Creating base tables")
        Item.__table__.create(bind=db.engine, checkfirst=True)
        Skill.__table__.create(bind=db.engine, checkfirst=True)
        
        # Create guild table
        logger.info("Creating guild table")
        Guild.__table__.create(bind=db.engine, checkfirst=True)
        
        # Create tables that depend on users and guilds
        logger.info("Creating dependent tables")
        Announcement.__table__.create(bind=db.engine, checkfirst=True)
        Party.__table__.create(bind=db.engine, checkfirst=True)
        Gate.__table__.create(bind=db.engine, checkfirst=True)
        MagicBeast.__table__.create(bind=db.engine, checkfirst=True)
        Mount.__table__.create(bind=db.engine, checkfirst=True)
        Pet.__table__.create(bind=db.engine, checkfirst=True)
        
        # Create inventory items after items table exists
        logger.info("Creating inventory related tables")
        InventoryItem.__table__.create(bind=db.engine, checkfirst=True)
        
        # Create quest related tables
        logger.info("Creating quest related tables")
        Quest.__table__.create(bind=db.engine, checkfirst=True)
        GuildQuest.__table__.create(bind=db.engine, checkfirst=True)
        
        # Create achievement and transaction tables last
        logger.info("Creating achievement and transaction tables")
        Achievement.__table__.create(bind=db.engine, checkfirst=True)
        Transaction.__table__.create(bind=db.engine, checkfirst=True)
        
        # Verify all tables were created
        inspector = inspect(db.engine)
        required_tables = ['users', 'wallets', 'announcements', 'guilds', 
                          'parties', 'gates', 'magic_beasts', 'inventory_items',
                          'items', 'mounts', 'pets', 'skills', 'quests',
                          'guild_quests', 'achievements', 'transactions']
        
        for table_name in required_tables:
            if not inspector.has_table(table_name):
                raise Exception(f"Failed to create table: {table_name}")

        logger.info("Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
