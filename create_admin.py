#!/usr/bin/env python3
import os
import bcrypt
from datetime import datetime
from dotenv import load_dotenv
from app import app
from models import User, PlayerCharacter, Wallet, Inventory
from database import db, init_db
import time

def create_admin_account():
    """Create the admin account with default credentials"""
    with app.app_context():
        try:
            # Initialize database and create tables
            print("Initializing database...")
            init_db(app)
            
            # Wait for tables to be ready
            max_attempts = 5
            attempt = 0
            while attempt < max_attempts:
                try:
                    # Check if tables exist
                    tables = db.engine.table_names()
                    if 'users' in tables:
                        print(f"Tables created: {', '.join(tables)}")
                        break
                    attempt += 1
                    if attempt == max_attempts:
                        raise Exception("Failed to create tables")
                    time.sleep(1)
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                    attempt += 1
                    if attempt == max_attempts:
                        raise
                    time.sleep(1)
            
            # Create admin user
            print("Creating admin user...")
            password = "admin123"  # Default password
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

            admin = User(
                username='admin',
                email='admin@terminusa.online',
                password=password_hash.decode('utf-8'),
                salt=salt.decode('utf-8'),
                role='admin',
                is_email_verified=True,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            
            db.session.add(admin)
            db.session.commit()  # Commit to get admin.id
            
            print("Creating admin character...")
            character = PlayerCharacter(
                user_id=admin.id,
                level=100,
                experience=0,
                rank='S',
                title='Administrator',
                strength=100,
                agility=100,
                intelligence=100,
                vitality=100,
                wisdom=100,
                hp=1000,
                mp=1000,
                physical_attack=100,
                magical_attack=100,
                physical_defense=100,
                magical_defense=100
            )
            db.session.add(character)
            db.session.commit()

            print("Creating admin wallet...")
            wallet = Wallet(
                user_id=admin.id,
                address=f"wallet_{os.urandom(8).hex()}",
                encrypted_privkey=os.urandom(32).hex(),
                iv=os.urandom(16).hex(),
                sol_balance=1000.0,
                crystals=100000,
                exons=100000
            )
            db.session.add(wallet)
            db.session.commit()

            print("Creating admin inventory...")
            inventory = Inventory(
                user_id=admin.id,
                max_slots=1000
            )
            db.session.add(inventory)
            db.session.commit()

            print("\nAdmin account created successfully!")
            print("----------------------------------------")
            print("Username: admin")
            print("Password: admin123")
            print("Email: admin@terminusa.online")
            print("Role: Administrator")
            print("Level: 100")
            print("Rank: S")
            print("Crystals: 100,000")
            print("Exons: 100,000")
            print("Inventory Slots: 1,000")
            print("----------------------------------------")
            print("IMPORTANT: Change the password after first login!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin account: {str(e)}")
            raise

if __name__ == "__main__":
    create_admin_account()
