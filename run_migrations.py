from alembic.config import Config
from alembic import command
import os

def run_migrations():
    """Run database migrations"""
    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    # Ensure migrations directory exists
    os.makedirs("migrations/versions", exist_ok=True)
    
    try:
        # Run the migration
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully!")
    except Exception as e:
        print(f"Error running migrations: {e}")
        raise

if __name__ == "__main__":
    run_migrations()
