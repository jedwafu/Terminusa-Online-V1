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
        
        # Import all models
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
        
        # Create tables in order
        logger.info("Creating tables in order")
        
        # Create independent tables first
        logger.info("Creating independent tables")
        tables_independent = [
            User.__table__,
            Item.__table__,
            Quest.__table__,
            Guild.__table__
        ]
        for table in tables_independent:
            table.create(bind=db.engine)
        
        # Create dependent tables
        logger.info("Creating dependent tables")
        tables_dependent = [
            Player.__table__,
            PlayerCharacter.__table__,
            Inventory.__table__,
            Equipment.__table__,
            Job.__table__,
            JobQuest.__table__,
            GamblingStats.__table__,
            Announcement.__table__,
            Achievement.__table__,
            Gate.__table__,
            GuildMember.__table__,
            GuildQuest.__table__,
            Mount.__table__,
            Pet.__table__,
            Currency.__table__,
            Party.__table__,
            PartyMember.__table__,
            PartyQuest.__table__,
            Friend.__table__,
            BlockedUser.__table__,
            PlayerProgress.__table__,
            ClassProgress.__table__,
            JobProgress.__table__,
            QuestProgress.__table__,
            Transaction.__table__,
            Wallet.__table__
        ]
        for table in tables_dependent:
            table.create(bind=db.engine)
        
        logger.info("Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
