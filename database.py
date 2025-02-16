from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.ext.declarative import declarative_base

# Create the SQLAlchemy instance
db = SQLAlchemy()
migrate = None

# Create declarative base
Base = declarative_base()

def init_db(app):
    """Initialize the database with the Flask app"""
    global migrate
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Bind the base to SQLAlchemy engine
    Base.metadata.bind = db.engine
    
    with app.app_context():
        # Import models to register them with SQLAlchemy
        import models
        
        # Create tables
        db.create_all()
        
        # Stamp the database with the latest migration
        from alembic.config import Config
        from alembic import command
        config = Config("alembic.ini")
        command.stamp(config, "head")
