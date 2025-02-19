from flask import Flask
from dotenv import load_dotenv
from database import db, init_db
import os

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database and create admin user"""
    print("Initializing database...")
    
    # Initialize Flask app
    app = Flask(__name__)

    # Configure app
    app.config.update(
        SECRET_KEY=os.getenv('FLASK_SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///terminusa.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Push application context
    ctx = app.app_context()
    ctx.push()

    # Initialize database
    init_db(app)

    try:
        # Import models after db initialization and within app context
        from models import User
        
        # Create database tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username=os.getenv('ADMIN_USERNAME', 'adminbb')).first()
        if not admin:
            admin = User(
                username=os.getenv('ADMIN_USERNAME', 'adminbb'),
                email=os.getenv('ADMIN_EMAIL', 'admin@terminusa.online'),
                role='admin',
                web3_wallet=os.getenv('ADMIN_WALLET', 'FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw')
            )
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise
    finally:
        # Pop the application context
        ctx.pop()

if __name__ == '__main__':
    init_database()
