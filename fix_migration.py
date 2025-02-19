from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def fix_migration():
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
            
            if current_version == '007_add_web3_and_announcements':
                # Update to new version
                db.session.execute("UPDATE alembic_version SET version_num = '008_add_game_models'")
                db.session.commit()
                print("Successfully updated version to 008_add_game_models")
            else:
                print(f"Unexpected version: {current_version}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    fix_migration()
