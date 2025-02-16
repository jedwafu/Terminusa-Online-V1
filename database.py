from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.ext.declarative import declarative_base
import time

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
    
    with app.app_context():
        # Import models to register them with SQLAlchemy
        import models
        
        # Bind the base to SQLAlchemy engine
        Base.metadata.bind = db.engine
        
        # Drop all tables
        db.drop_all()
        
        # Create tables
        db.create_all()
        
        # Verify tables are created
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            try:
                # Try to list tables
                tables = db.engine.table_names()
                app.logger.info(f"Created tables: {', '.join(tables)}")
                break
            except Exception as e:
                attempt += 1
                if attempt == max_attempts:
                    app.logger.error(f"Failed to create tables after {max_attempts} attempts: {str(e)}")
                    raise
                time.sleep(1)  # Wait before retrying
        
        try:
            # Stamp the database with the latest migration
            from alembic.config import Config
            from alembic import command
            config = Config("alembic.ini")
            command.stamp(config, "head")
        except Exception as e:
            app.logger.warning(f"Could not stamp database version: {str(e)}")
            # Continue anyway as this is not critical
            pass

def get_db():
    """Get database instance"""
    return db
