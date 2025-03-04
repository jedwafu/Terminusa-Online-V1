"""
Script to run the country fields migration
"""
from flask import Flask
from flask_migrate import Migrate, upgrade
from models import db
import config

def run_migration():
    """Run the migration to add country fields"""
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    with app.app_context():
        # Run the migration
        upgrade()
        print("Successfully added country fields to User and Guild models")

if __name__ == '__main__':
    run_migration()
