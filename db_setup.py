#!/usr/bin/env python3
import os
import sys
import argparse
from typing import Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Base, User, UserRole
import bcrypt
from datetime import datetime
import json

class DatabaseSetup:
    """Database setup and initialization"""
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData()

    def create_tables(self) -> bool:
        """Create all database tables"""
        try:
            Base.metadata.create_all(self.engine)
            print("Tables created successfully")
            return True
        except SQLAlchemyError as e:
            print(f"Error creating tables: {e}")
            return False

    def drop_tables(self) -> bool:
        """Drop all database tables"""
        try:
            Base.metadata.drop_all(self.engine)
            print("Tables dropped successfully")
            return True
        except SQLAlchemyError as e:
            print(f"Error dropping tables: {e}")
            return False

    def create_admin_user(
        self,
        username: str,
        email: str,
        password: str
    ) -> Optional[User]:
        """Create admin user"""
        try:
            session = self.Session()
            
            # Hash password
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                salt
            ).decode('utf-8')
            
            # Create admin user
            admin = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=UserRole.ADMIN,
                level=100,
                gold=1000000,
                crystals=10000,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                is_active=True,
                settings={
                    'notifications': True,
                    'theme': 'dark',
                    'language': 'en'
                }
            )
            
            session.add(admin)
            session.commit()
            
            print(f"Admin user '{username}' created successfully")
            return admin
            
        except SQLAlchemyError as e:
            print(f"Error creating admin user: {e}")
            session.rollback()
            return None
            
        finally:
            session.close()

    def create_test_data(self) -> bool:
        """Create test data"""
        try:
            session = self.Session()
            
            # Create test users
            test_users = []
            for i in range(1, 6):
                user = User(
                    username=f"test_user_{i}",
                    email=f"test{i}@example.com",
                    password_hash=bcrypt.hashpw(
                        f"password{i}".encode('utf-8'),
                        bcrypt.gensalt()
                    ).decode('utf-8'),
                    role=UserRole.PLAYER,
                    level=i * 10,
                    experience=i * 1000,
                    gold=i * 1000,
                    crystals=i * 100,
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow(),
                    is_active=True,
                    settings={
                        'notifications': True,
                        'theme': 'light',
                        'language': 'en'
                    }
                )
                test_users.append(user)
            
            session.add_all(test_users)
            session.commit()
            
            print("Test data created successfully")
            return True
            
        except SQLAlchemyError as e:
            print(f"Error creating test data: {e}")
            session.rollback()
            return False
            
        finally:
            session.close()

    def verify_database(self) -> bool:
        """Verify database setup"""
        try:
            session = self.Session()
            
            # Check connection
            session.execute("SELECT 1")
            
            # Check tables
            for table in Base.metadata.tables:
                if not self.engine.dialect.has_table(
                    self.engine,
                    table
                ):
                    print(f"Table '{table}' not found")
                    return False
            
            # Check admin user
            admin = session.query(User).filter_by(
                role=UserRole.ADMIN
            ).first()
            if not admin:
                print("Admin user not found")
                return False
            
            print("Database verification successful")
            return True
            
        except SQLAlchemyError as e:
            print(f"Database verification failed: {e}")
            return False
            
        finally:
            session.close()

    def reset_database(self) -> bool:
        """Reset database to initial state"""
        try:
            # Drop and recreate tables
            if not self.drop_tables():
                return False
            if not self.create_tables():
                return False
            
            # Create admin user
            if not self.create_admin_user(
                "admin",
                "admin@terminusa.com",
                "admin123"
            ):
                return False
            
            # Create test data
            if not self.create_test_data():
                return False
            
            print("Database reset successful")
            return True
            
        except Exception as e:
            print(f"Error resetting database: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Database setup utility'
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database to initial state'
    )
    
    parser.add_argument(
        '--create-tables',
        action='store_true',
        help='Create database tables'
    )
    
    parser.add_argument(
        '--drop-tables',
        action='store_true',
        help='Drop database tables'
    )
    
    parser.add_argument(
        '--create-admin',
        action='store_true',
        help='Create admin user'
    )
    
    parser.add_argument(
        '--create-test-data',
        action='store_true',
        help='Create test data'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify database setup'
    )
    
    parser.add_argument(
        '--db-url',
        default=os.getenv(
            'DB_URL',
            'sqlite:///terminusa.db'
        ),
        help='Database URL'
    )
    
    args = parser.parse_args()
    
    # Create database setup instance
    db_setup = DatabaseSetup(args.db_url)
    
    # Process commands
    if args.reset:
        if not db_setup.reset_database():
            sys.exit(1)
    
    if args.create_tables:
        if not db_setup.create_tables():
            sys.exit(1)
    
    if args.drop_tables:
        if not db_setup.drop_tables():
            sys.exit(1)
    
    if args.create_admin:
        if not db_setup.create_admin_user(
            "admin",
            "admin@terminusa.com",
            "admin123"
        ):
            sys.exit(1)
    
    if args.create_test_data:
        if not db_setup.create_test_data():
            sys.exit(1)
    
    if args.verify:
        if not db_setup.verify_database():
            sys.exit(1)
    
    print("Database setup completed successfully")

if __name__ == '__main__':
    main()
