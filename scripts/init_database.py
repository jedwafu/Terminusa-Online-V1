"""
Database initialization script.
Creates all tables and initializes default data.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from flask import Flask
from database import db
from models import init_db
from alembic import command
from alembic.config import Config

def create_app():
    """Create Flask app for database initialization"""
    app = Flask(__name__)
    
    # Configure app
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    # Initialize extensions
    db.init_app(app)
    
    return app

def init_database():
    """Initialize database with all tables and default data"""
    try:
        print("Starting database initialization...")
        
        # Create Flask app
        app = create_app()
        
        with app.app_context():
            # Run migrations
            print("Running database migrations...")
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            
            # Initialize models with default data
            print("Initializing default data...")
            init_db()
            
            print("Database initialization complete!")
            return True
            
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

def verify_database():
    """Verify database initialization"""
    try:
        print("Verifying database initialization...")
        
        app = create_app()
        
        with app.app_context():
            # Check if tables exist
            print("Checking database tables...")
            tables = db.engine.table_names()
            required_tables = [
                'currencies', 'transactions', 'token_swaps',
                'items', 'inventories', 'equipment',
                'ai_models', 'ai_training_data', 'ai_evaluations',
                'player_activities', 'player_characters', 'player_skills',
                'skills', 'job_history', 'job_quests',
                'gates', 'magic_beasts', 'gate_sessions',
                'ai_behaviors', 'guilds', 'guild_members',
                'parties', 'party_members', 'friends',
                'achievements', 'quests', 'quest_progress',
                'quest_rewards', 'milestones', 'user_milestones'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                print(f"Missing tables: {missing_tables}")
                return False
            
            # Check if default data exists
            print("Checking default data...")
            from models import (
                Currency, Item, AIModel,
                Achievement, Milestone
            )
            
            checks = [
                (Currency, 'currencies'),
                (Item, 'items'),
                (AIModel, 'AI models'),
                (Achievement, 'achievements'),
                (Milestone, 'milestones')
            ]
            
            for model, name in checks:
                count = model.query.count()
                if count == 0:
                    print(f"No default {name} found")
                    return False
                print(f"Found {count} {name}")
            
            print("Database verification complete!")
            return True
            
    except Exception as e:
        print(f"Error verifying database: {str(e)}")
        return False

if __name__ == '__main__':
    # Check if --verify flag is passed
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        success = verify_database()
    else:
        success = init_database()
        if success:
            success = verify_database()
    
    sys.exit(0 if success else 1)
