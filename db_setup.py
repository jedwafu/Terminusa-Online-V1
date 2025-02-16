from typing import Optional, Dict, Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Base, User, UserRole
import bcrypt
from datetime import datetime
import json
import os
import sys

# Create the SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    with app.app_context():
        db.create_all()

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
            
            # Generate salt and hash password
            salt = os.urandom(16).hex()
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Create admin user
            admin = User(
                username=username,
                email=email,
                password=password_hash,
                salt=salt,
                role='admin',
                is_email_verified=True,
                created_at=datetime.utcnow()
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
                salt = os.urandom(16).hex()
                password_hash = bcrypt.hashpw(
                    f"password{i}".encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                user = User(
                    username=f"test_user_{i}",
                    email=f"test{i}@example.com",
                    password=password_hash,
                    salt=salt,
                    role='player',
                    is_email_verified=True,
                    created_at=datetime.utcnow()
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
                role='admin'
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

if __name__ == '__main__':
    # Get database URL from environment or use default
    db_url = os.getenv('DATABASE_URL', 'sqlite:///terminusa.db')
    
    # Create database setup instance
    db_setup = DatabaseSetup(db_url)
    
    # Reset database (drop all tables, recreate them, and add initial data)
    if db_setup.reset_database():
        print("Database setup completed successfully")
    else:
        print("Database setup failed")
        sys.exit(1)
