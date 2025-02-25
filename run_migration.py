from migrations.initial_migration import initialize_database
from database import db
from web_app import create_app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        try:
            initialize_database()
            print("Database migration completed successfully!")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
