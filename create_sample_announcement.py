from app import app, db
from models import Announcement
from datetime import datetime

def create_sample_announcement():
    with app.app_context():
        # Create a sample announcement
        announcement = Announcement(
            title="Welcome to the New Terminusa Online",
            content="""
            We're excited to announce the launch of our new website design! 
            
            Key features:
            - Modern cyberpunk theme
            - Improved navigation
            - Better mobile experience
            - Real-time updates
            
            Stay tuned for more updates and features coming soon!
            """,
            created_at=datetime.utcnow()
        )
        
        # Add to database
        db.session.add(announcement)
        db.session.commit()
        
        print("Sample announcement created successfully!")

if __name__ == "__main__":
    create_sample_announcement()
