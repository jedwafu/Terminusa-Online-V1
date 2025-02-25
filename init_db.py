from web_app import create_app
from models import db

def initialize_database():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        # Create tables in specific order to handle dependencies
        db.metadata.create_all(bind=db.engine, tables=[
            db.metadata.tables['users'],
            db.metadata.tables['player_characters'],
            db.metadata.tables['wallets'],
            db.metadata.tables['announcements']
        ])
        print("[INFO] Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
