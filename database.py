from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import time

# Create the SQLAlchemy instance
db = SQLAlchemy()
migrate = None

def init_db(app):
    """Initialize the database with the Flask app"""
    global migrate
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    with app.app_context():
        # Import models to register them with SQLAlchemy
        import models
        
        try:
            # Drop all tables
            db.drop_all()
            app.logger.info("Dropped all existing tables")
            
            # Create all tables
            db.create_all()
            app.logger.info("Created all tables")
            
            # Verify tables are created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            app.logger.info(f"Created tables: {', '.join(tables)}")
            
            # Verify specific tables exist
            required_tables = ['users', 'player_characters', 'wallets', 'inventories']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                raise Exception(f"Missing required tables: {', '.join(missing_tables)}")
            
            # Create extensions
            db.session.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            db.session.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
            db.session.commit()
            
            return True
            
        except Exception as e:
            app.logger.error(f"Error initializing database: {str(e)}")
            db.session.rollback()
            raise
