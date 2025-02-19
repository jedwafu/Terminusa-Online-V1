from flask import Flask
from dotenv import load_dotenv
from database import db, init_db
import os

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database and create admin user"""
    print("Initializing database...")
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    init_db(app)
    
    # Import models after database initialization
    from models import User
    
    # Create admin user if it doesn't exist
    with app.app_context():
        admin = User.query.filter_by(username=os.getenv('ADMIN_USERNAME', 'adminbb')).first()
        if not admin:
            admin = User(
                username=os.getenv('ADMIN_USERNAME', 'adminbb'),
                email=os.getenv('ADMIN_EMAIL', 'admin@terminusa.online'),
                role='admin'
            )
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'Jeidel123'))
            admin.web3_wallet = os.getenv('ADMIN_WALLET', 'FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
    
    print("Database initialized successfully")
    return app

def print_users_table_columns(app):
    """Print the columns of the users table"""
    with app.app_context():
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('users')
        print("\nUsers table columns:")
        for column in columns:
            print(f"- {column['name']}: {column['type']}")

if __name__ == '__main__':
    app = init_database()  # Get the app instance from init_database
    print_users_table_columns(app)  # Pass the app instance to the function
