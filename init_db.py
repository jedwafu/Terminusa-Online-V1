import logging
import os
from web_app import create_app
from database import db

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
        
        # Import all models to ensure they're registered
        from models import (
            User,
            Player,
            PlayerCharacter,
            Inventory,
            Item,
            Equipment,
            Job,
            JobQuest,
            GamblingStats,
            Announcement,
            Achievement,
            Gate,
            Guild,
            GuildMember,
            GuildQuest,
            Mount,
            Pet,
            Currency,
            Party,
            PartyMember,
            PartyQuest,
            Friend,
            BlockedUser,
            PlayerProgress,
            ClassProgress,
            JobProgress,
            Quest,
            QuestProgress,
            Transaction,
            Wallet
        )
        
        # Drop all existing tables
        logger.info("Dropping all existing tables")
        db.drop_all()
        
        # Create all tables
        logger.info("Creating all tables")
        db.create_all()
        
        logger.info("Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
