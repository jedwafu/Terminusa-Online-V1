from db_setup import DatabaseSetup
import os

# Get database URL from environment or use default
db_url = os.getenv('DB_URL', 'sqlite:///terminusa.db')

# Initialize database setup
db_setup = DatabaseSetup(db_url)

# Reset database (drop all tables, recreate them, and add initial data)
if db_setup.reset_database():
    print("Database reset completed successfully")
else:
    print("Database reset failed")
