from flask import Flask
from dotenv import load_dotenv
from database import db, init_db
from models import User, Announcement
import os

# Load environment variables
load_dotenv()

def create_sample_announcement():
    """Create a sample announcement"""
    print("Creating sample announcement...")
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    init_db(app)
    
    with app.app_context():
        # Get admin user
        admin = User.query.filter_by(username=os.getenv('ADMIN_USERNAME', 'adminbb')).first()
        if not admin:
            print("Error: Admin user not found!")
            return
        
        # Create announcement
        announcement = Announcement(
            title="Welcome to Terminusa Online",
            content="Welcome to Terminusa Online! We're excited to have you join our community. Get ready for an epic adventure!",
            author_id=admin.id,
            is_active=True,
            priority=1
        )
        
        db.session.add(announcement)
        db.session.commit()
        print("Sample announcement created successfully!")

if __name__ == '__main__':
    create_sample_announcement()
