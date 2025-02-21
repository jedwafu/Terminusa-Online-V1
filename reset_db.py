"""
Reset database script for fresh migration
"""
from app import app
from models import db
from sqlalchemy import text

def reset_database():
    """Drop all tables and reset migrations"""
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Drop alembic_version table
        with db.engine.connect() as conn:
            conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
            conn.commit()
        
        print("Database reset complete")

if __name__ == "__main__":
    reset_database()
