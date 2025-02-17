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
            # Check if tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                app.logger.info("No existing tables found. Creating tables...")
                db.create_all()
                app.logger.info("Created all tables")
            else:
                app.logger.info(f"Found existing tables: {', '.join(existing_tables)}")
                
                # Verify required tables exist
                required_tables = ['users', 'player_characters', 'wallets', 'inventories']
                missing_tables = [table for table in required_tables if table not in existing_tables]
                
                if missing_tables:
                    app.logger.warning(f"Missing required tables: {', '.join(missing_tables)}")
                    app.logger.info("Creating missing tables...")
                    db.create_all()  # This will only create missing tables
                    app.logger.info("Created missing tables")
            
            # Create extensions if they don't exist
            db.session.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            db.session.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
            db.session.commit()
            
            # Verify tables after creation
            final_tables = db.engine.table_names()
            app.logger.info(f"Available tables: {', '.join(final_tables)}")
            
            return True
            
        except Exception as e:
            app.logger.error(f"Error initializing database: {str(e)}")
            db.session.rollback()
            raise

def get_db():
    """Get database instance"""
    return db
