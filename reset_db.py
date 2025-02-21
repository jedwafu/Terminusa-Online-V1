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
        # Drop all tables and types with foreign key checks disabled
        with db.engine.connect() as conn:
            # Drop all tables
            conn.execute(text("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """))

            # Drop all enum types
            conn.execute(text("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT typname FROM pg_type WHERE typnamespace = 'public'::regnamespace AND typtype = 'e') LOOP
                        EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
                    END LOOP;
                END $$;
            """))

            # Drop alembic_version table
            conn.execute(text('DROP TABLE IF EXISTS alembic_version;'))
            
            conn.commit()
        
        print("Database reset complete")

if __name__ == "__main__":
    reset_database()
