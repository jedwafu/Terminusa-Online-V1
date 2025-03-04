"""
Create the announcements table directly using SQL
"""
import os
import psycopg2
from dotenv import load_dotenv

def create_announcements_table():
    """Create the announcements table using direct SQL"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get database connection parameters from environment
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("DATABASE_URL not found in environment variables")
            return False
        
        # Connect to the database
        print(f"Connecting to database: {db_url}")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if the table exists
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'announcements')")
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("Creating announcements table...")
            
            # Create the table
            cursor.execute("""
            CREATE TABLE announcements (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                author_id INTEGER,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                last_accessed_at TIMESTAMP WITHOUT TIME ZONE,
                last_modified_at TIMESTAMP WITHOUT TIME ZONE,
                CONSTRAINT fk_announcement_author FOREIGN KEY (author_id) REFERENCES users(id)
            );
            
            CREATE INDEX ix_announcements_created_at ON announcements (created_at);
            CREATE INDEX ix_announcements_priority ON announcements (priority);
            """)
            
            print("Announcements table created successfully!")
        else:
            print("Announcements table already exists.")
        
        # Close the connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error creating announcements table: {str(e)}")
        return False

if __name__ == "__main__":
    create_announcements_table()
