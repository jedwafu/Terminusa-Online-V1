"""
Database initialization script for Terminusa Online
"""
from app import app, db
from models import init_models

def init_database():
    """Initialize the database"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize model relationships
        init_models()
        
        print("Database initialized successfully")

if __name__ == "__main__":
    init_database()
