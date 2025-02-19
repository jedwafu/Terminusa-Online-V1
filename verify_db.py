from flask import Flask
from dotenv import load_dotenv
from database import db, init_db
from models import User
import os

# Load environment variables
load_dotenv()

def verify_database():
    """Verify database initialization and admin user creation"""
    print("Verifying database...")
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    init_db(app)
    
    with app.app_context():
        # Check admin user
        admin = User.query.filter_by(username=os.getenv('ADMIN_USERNAME', 'adminbb')).first()
        if admin:
            print(f"\nAdmin user exists:")
            print(f"- Username: {admin.username}")
            print(f"- Email: {admin.email}")
            print(f"- Role: {admin.role}")
            print(f"- Level: {admin.level}")
            print(f"- Hunter Class: {admin.hunter_class}")
        else:
            print("Admin user not found!")
        
        # Check table columns
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('users')
        print("\nUsers table columns:")
        for column in columns:
            print(f"- {column['name']}: {column['type']}")

if __name__ == '__main__':
    verify_database()
