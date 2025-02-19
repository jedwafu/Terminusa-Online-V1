import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_migration():
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    
    try:
        # Connect to the database
        conn = psycopg2.connect(db_url)
        conn.autocommit = True  # Set autocommit mode
        
        # Create a cursor
        cur = conn.cursor()
        
        # First check current version
        cur.execute("SELECT version_num FROM alembic_version")
        current_version = cur.fetchone()[0]
        print(f"Current version: {current_version}")
        
        if current_version == '007_add_web3_and_announcements':
            # Update to new version
            cur.execute("UPDATE alembic_version SET version_num = '008_add_game_models'")
            print("Successfully updated version to 008_add_game_models")
        else:
            print(f"Unexpected version: {current_version}")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == '__main__':
    fix_migration()
