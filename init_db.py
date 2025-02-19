import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure app
app.config.update(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY'),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Import models after db initialization
from models import *

# Initialize Flask-Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
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
        
        print("Database initialized")
