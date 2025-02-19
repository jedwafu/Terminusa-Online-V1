from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def check_alembic():
    # Initialize Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy
    db = SQLAlchemy(app)
    
    try:
        with app.app_context():
            # Check alembic_version table
            result = db.session.execute(text("SELECT version_num FROM alembic_version"))
            versions = [row[0] for row in result]
            print("Current versions:", versions)
            
            # Check users table columns
            result = db.session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
            """))
            columns = [(row[0], row[1]) for row in result]
            print("\nUsers table columns:")
            for col, type_ in columns:
                print(f"- {col}: {type_}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    check_alembic()
