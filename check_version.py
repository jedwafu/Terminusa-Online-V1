from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def check_version():
    # Initialize Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # Execute raw SQL to check current version
            result = db.session.execute("SELECT version_num FROM alembic_version")
            current_version = result.scalar()
            print(f"Current version: {current_version}")
            
            # Update to correct version if needed
            if current_version != '008_add_game_models':
                db.session.execute("UPDATE alembic_version SET version_num = '008_add_game_models'")
                db.session.commit()
                print("Updated version to 008_add_game_models")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    check_version()
