from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

db = SQLAlchemy()

def init_db(app):
    """Initialize the database connection"""
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    db.session = scoped_session(sessionmaker(autocommit=False,
                                            autoflush=False,
                                            bind=engine))
    db.Model.metadata.create_all(bind=engine)

def init_db(app):
    """Initialize the database"""
    db.init_app(app)
    with app.app_context():
        # Import all models to ensure they're registered
        from models.user import User
        from models.player import PlayerCharacter
        from models import Wallet
        from models.announcement import Announcement
        
        # Create tables in explicit order with proper registration
        from models.user import User
        User.__table__.create(bind=db.engine, checkfirst=True)
        
        from models import Wallet
        Wallet.__table__.create(bind=db.engine, checkfirst=True)
        
        from models.player import PlayerCharacter
        PlayerCharacter.__table__.create(bind=db.engine, checkfirst=True)
        
        from models.announcement import Announcement
        Announcement.__table__.create(bind=db.engine, checkfirst=True)
