"""
Reset database script for fresh migration
"""
from app import create_app
from models import db
from sqlalchemy import text

def reset_database():
    """Drop all tables and reset migrations"""
    app = create_app()
    with app.app_context():
        # Drop all tables with foreign key checks disabled
        with db.engine.connect() as conn:
            # Disable foreign key checks
            conn.execute(text('SET FOREIGN_KEY_CHECKS=0;')) if 'mysql' in str(db.engine.url) else conn.execute(text('SET CONSTRAINTS ALL DEFERRED;'))
            
            # Get all table names
            if 'mysql' in str(db.engine.url):
                result = conn.execute(text('SHOW TABLES;'))
                tables = [row[0] for row in result]
            else:
                result = conn.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public';
                """))
                tables = [row[0] for row in result]
            
            # Drop each table
            for table in tables:
                conn.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE;'))
            
            # Drop alembic_version table
            conn.execute(text('DROP TABLE IF EXISTS alembic_version;'))
            
            # Re-enable foreign key checks
            conn.execute(text('SET FOREIGN_KEY_CHECKS=1;')) if 'mysql' in str(db.engine.url) else conn.execute(text('SET CONSTRAINTS ALL IMMEDIATE;'))
            
            conn.commit()
        
        print("Database reset complete")

if __name__ == "__main__":
    reset_database()
