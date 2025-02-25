from migrations.initial_migration import initialize_database
from database import db
from web_app import create_app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("WARNING: This will DROP ALL EXISTING TABLES and recreate the database.")
        confirmation = input("Are you sure you want to continue? (yes/no): ")
        
        if confirmation.lower() == 'yes':
            try:
                initialize_database()
                print("Database migration completed successfully!")
            except Exception as e:
                print(f"Error during migration: {str(e)}")
        else:
            print("Migration cancelled.")
