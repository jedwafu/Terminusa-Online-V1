from web_app import create_app
from models import db

def initialize_database():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        
        # Create tables in specific order to handle dependencies
        from models import (
            User, 
            Wallet,
            Announcement,
            Guild,
            Party,
            Gate,
            MagicBeast,
            InventoryItem,
            Item,
            Mount,
            Pet,
            Skill,
            Quest,
            GuildQuest,
            Achievement,
            Transaction
        )
        
        # Create tables using raw SQL commands
        with db.engine.connect() as connection:
            # Create users table
            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(128),
                    web3_wallet VARCHAR(64),
                    role VARCHAR(20) DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Create wallets table without foreign key first
            connection.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    solana_address VARCHAR(64),
                    solana_balance FLOAT DEFAULT 0.0,
                    exons_balance FLOAT DEFAULT 0.0,
                    crystals_balance INTEGER DEFAULT 0,
                    is_blockchain BOOLEAN DEFAULT TRUE,
                    max_supply BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add foreign key constraint after both tables exist
            connection.execute("""
                ALTER TABLE wallets 
                ADD CONSTRAINT fk_wallets_users 
                FOREIGN KEY (user_id) 
                REFERENCES users(id)
            """)
        
        print("[INFO] Database initialized successfully")

if __name__ == '__main__':
    print("[INFO] Initializing database...")
    initialize_database()
