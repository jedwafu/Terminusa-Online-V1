import os
from flask_migrate import Migrate, init, migrate, upgrade
from app import app, db

def run_migrations():
    """Run database migrations"""
    try:
        # Set up application context
        with app.app_context():
            # Initialize Flask-Migrate
            migrate = Migrate(app, db)
            
            # Initialize migrations directory if it doesn't exist
            if not os.path.exists("migrations"):
                print("Initializing migrations directory...")
                init()
            
            # Create migration
            print("Creating migration...")
            migrate()
            
            # Apply migration
            print("Applying migration...")
            upgrade()
            
            print("Migrations completed successfully!")
    except Exception as e:
        print(f"Error running migrations: {e}")
        raise

if __name__ == "__main__":
    run_migrations()
