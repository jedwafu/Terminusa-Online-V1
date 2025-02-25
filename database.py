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
        
        # Create tables in strict dependency order
        User.__table__.create(bind=db.engine, checkfirst=True)
        Wallet.__table__.create(bind=db.engine, checkfirst=True)
        PlayerCharacter.__table__.create(bind=db.engine, checkfirst=True)
        Announcement.__table__.create(bind=db.engine, checkfirst=True)
