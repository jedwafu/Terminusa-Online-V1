from app_new import app, db
from models import Announcement
from datetime import datetime

def create_initial_announcement():
    with app.app_context():
        try:
            # Create the announcements table if it doesn't exist
            db.create_all()
            
            # Create a welcome announcement
            announcement = Announcement(
                title="Welcome to the New Terminusa Online",
                content="""
                Welcome to the newly redesigned Terminusa Online! 🎮
                
                We're excited to introduce our modern, cyberpunk-themed interface with several new features:
                
                ✨ New Features:
                - Modern, responsive design
                - Improved navigation
                - Enhanced marketplace
                - Real-time notifications
                - Better mobile experience
                
                🛠️ Technical Improvements:
                - Faster page loads
                - Better security
                - Improved error handling
                - Enhanced stability
                
                Stay tuned for more updates and features coming soon!
                
                ~ The Terminusa Team
                """,
                created_at=datetime.utcnow()
            )
            
            # Add to database
            db.session.add(announcement)
            db.session.commit()
            
            print("Initial announcement created successfully!")
            
        except Exception as e:
            print(f"Error creating announcement: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_initial_announcement()
