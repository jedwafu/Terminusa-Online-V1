"""
Create the announcements table directly using SQLAlchemy
"""
from flask import Flask
from database import db
from models.announcement import Announcement
import os

def create_announcements_table():
    """Create the announcements table if it doesn't exist"""
    try:
        # Create a minimal Flask app
        app = Flask(__name__)
        
        # Configure the app
        app.config.update(
            SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
        
        # Initialize the database
        db.init_app(app)
        
        # Create the announcements table
        with app.app_context():
            # Check if the table exists
            inspector = db.inspect(db.engine)
            if 'announcements' not in inspector.get_table_names():
                print("Creating announcements table...")
                
                # Create the table
                Announcement.__table__.create(db.engine)
                print("Announcements table created successfully!")
            else:
                print("Announcements table already exists.")
        
        return True
    except Exception as e:
        print(f"Error creating announcements table: {str(e)}")
        return False

if __name__ == "__main__":
    create_announcements_table()
