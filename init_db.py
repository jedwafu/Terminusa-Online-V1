"""
Database initialization script for Terminusa Online
"""
from web_app import create_app
from models import db, init_models

def init_database():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize model relationships
        init_models()
        
        print("Database initialized successfully")

if __name__ == "__main__":
    init_database()