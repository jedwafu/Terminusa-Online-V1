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
        
        # Ensure all models are registered first
        from models import User, PlayerCharacter, Wallet, Announcement
        
        # Create tables in specific order to handle dependencies
        db.metadata.create_all(bind=db.engine, tables=[
            User.__table__,
            PlayerCharacter.__table__,
            Wallet.__table__,
            Announcement.__table__
        ], checkfirst=True)
