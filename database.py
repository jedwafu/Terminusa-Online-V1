from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize the database"""
    db.init_app(app)
    with app.app_context():
        # Import all models to ensure they're registered
        from models.user import User
        from models.player import PlayerCharacter
        from models import Wallet
        from models.announcement import Announcement
        
        # Create tables in specific order to handle dependencies
        db.metadata.create_all(bind=db.engine, tables=[
            db.metadata.tables['users'],
            db.metadata.tables['player_characters'],
            db.metadata.tables['wallets'],
            db.metadata.tables['announcements']
        ])
