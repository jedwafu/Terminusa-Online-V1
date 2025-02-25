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
        
        # Ensure User model is properly registered
        User.__table__.create(bind=db.engine, checkfirst=True)
        
        # Create remaining tables
        db.metadata.create_all(bind=db.engine, tables=[
            Wallet.__table__,
            PlayerCharacter.__table__,
            Announcement.__table__
        ], checkfirst=True)
