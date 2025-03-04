"""
Initialize and run database migrations for adding country fields
"""
import os
from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade
from models import db
import config

def init_migrations():
    """Initialize and run migrations"""
    try:
        # Create Flask app
        app = Flask(__name__)
        app.config.from_object(config)
        
        # Initialize database
        db.init_app(app)
        
        with app.app_context():
            # Initialize Flask-Migrate
            migrate = Migrate(app, db)
            
            # Check if migrations directory exists
            if not os.path.exists('migrations'):
                print("Initializing migrations directory...")
                init()
            
            # Create migration
            print("Creating migration for country fields...")
            migrate()
            
            # Apply migration
            print("Applying migration...")
            upgrade()
            
            print("Successfully added country fields to User and Guild models")
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise

if __name__ == '__main__':
    init_migrations()
