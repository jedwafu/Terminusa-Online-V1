"""
Reset database script for fresh migration
"""
from app import app, db
from sqlalchemy import text

def reset_database():
    """Drop all tables and reset migrations"""
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Drop alembic_version table
        db.engine.execute(text('DROP TABLE IF EXISTS alembic_version'))
        
        print("Database reset complete")

if __name__ == "__main__":
    reset_database()
