from typing import Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from database import db
from models import (
    User, PlayerCharacter, PlayerSkill, Wallet, Item, 
    Inventory, InventoryItem, Guild, GuildMember, Party, 
    PartyMember, PartyInvitation, Gate, GateSession, 
    MagicBeast, Achievement, AIBehavior, Transaction, 
    ChatMessage, GateType
)
import bcrypt
from datetime import datetime
import os
import sys
import secrets

class DatabaseSetup:
    """Database setup and initialization"""
    def __init__(self, app):
        self.app = app

    def create_tables(self) -> bool:
        """Create all database tables"""
        try:
            with self.app.app_context():
                db.create_all()
            print("Tables created successfully")
            return True
        except SQLAlchemyError as e:
            print(f"Error creating tables: {e}")
            return False

    def drop_tables(self) -> bool:
        """Drop all database tables"""
        try:
            with self.app.app_context():
                db.drop_all()
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
            with self.app.app_context():
                # Generate salt and hash password
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(
                    password.encode('utf-8'),
                    salt
                ).decode('utf-8')
                
                # Create admin user
                admin = User(
                    username=username,
                    email=email,
                    password=password_hash,
                    salt=salt.decode('utf-8'),
                    role='admin',
                    is_email_verified=True,
                    created_at=datetime.utcnow(),
                    last_login=datetime.utcnow()
                )
                
                db.session.add(admin)
                db.session.flush()  # Get admin.id

                # Create character
                character = PlayerCharacter(
                    user_id=admin.id,
                    level=100,
                    experience=0,
                    rank='S',
                    title='Administrator',
                    strength=1000,
                    agility=1000,
                    intelligence=1000,
                    vitality=1000,
                    wisdom=1000
                )
                db.session.add(character)

                # Create wallet for admin
                wallet = Wallet(
                    user_id=admin.id,
                    address=f"admin_wallet_{secrets.token_hex(8)}",
                    encrypted_privkey=secrets.token_hex(32),
                    iv=secrets.token_hex(16),
                    sol_balance=1000.0,
                    crystals=1000000,
                    exons=1000000
                )
                db.session.add(wallet)

                # Create inventory for admin
                inventory = Inventory(
                    user_id=admin.id,
                    max_slots=1000
                )
                db.session.add(inventory)

                db.session.commit()
                
                print(f"Admin user '{username}' created successfully")
                return admin
            
        except SQLAlchemyError as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()
            return None

    def create_test_data(self) -> bool:
        """Create test data"""
        try:
            with self.app.app_context():
                # Create test users
                for i in range(1, 6):
                    # Generate salt and hash password
                    salt = bcrypt.gensalt()
                    password_hash = bcrypt.hashpw(
                        f"password{i}".encode('utf-8'),
                        salt
                    ).decode('utf-8')
                    
                    # Create user
                    user = User(
                        username=f"test_user_{i}",
                        email=f"test{i}@terminusa.online",
                        password=password_hash,
                        salt=salt.decode('utf-8'),
                        role='player',
                        is_email_verified=True,
                        created_at=datetime.utcnow(),
                        last_login=datetime.utcnow()
                    )
                    
                    db.session.add(user)
                    db.session.flush()  # Get user.id

                    # Create character
                    character = PlayerCharacter(
                        user_id=user.id,
                        level=1,
                        experience=0,
                        rank='F',
                        title='Novice Hunter'
                    )
                    db.session.add(character)

                    # Create wallet
                    wallet = Wallet(
                        user_id=user.id,
                        address=f"wallet_{secrets.token_hex(8)}",
                        encrypted_privkey=secrets.token_hex(32),
                        iv=secrets.token_hex(16),
                        sol_balance=0.0,
                        crystals=int(os.getenv('STARTING_CRYSTALS', 20)),
                        exons=int(os.getenv('STARTING_EXONS', 0))
                    )
                    db.session.add(wallet)

                    # Create inventory
                    inventory = Inventory(
                        user_id=user.id,
                        max_slots=int(os.getenv('STARTING_INVENTORY_SLOTS', 20))
                    )
                    db.session.add(inventory)

                # Create some initial gates
                gates = [
                    {
                        'name': 'Training Ground',
                        'description': 'A basic gate for novice hunters',
                        'type': GateType.NORMAL,
                        'level_requirement': 1,
                        'rank_requirement': 'F',
                        'monster_level': 1,
                        'monster_rank': 'F',
                        'rewards': {
                            'experience': 100,
                            'crystals': 10,
                            'items': ['Basic Potion', 'Wooden Sword']
                        }
                    },
                    {
                        'name': 'Forest of Trials',
                        'description': 'A mysterious forest gate',
                        'type': GateType.ELITE,
                        'level_requirement': 5,
                        'rank_requirement': 'F',
                        'monster_level': 5,
                        'monster_rank': 'F',
                        'rewards': {
                            'experience': 500,
                            'crystals': 50,
                            'items': ['Healing Potion', 'Iron Sword']
                        }
                    },
                    {
                        'name': 'Demon\'s Lair',
                        'description': 'A dangerous gate with powerful enemies',
                        'type': GateType.BOSS,
                        'level_requirement': 10,
                        'rank_requirement': 'E',
                        'monster_level': 10,
                        'monster_rank': 'E',
                        'rewards': {
                            'experience': 1000,
                            'crystals': 100,
                            'items': ['Greater Healing Potion', 'Steel Sword']
                        }
                    }
                ]

                for gate_data in gates:
                    gate = Gate(
                        name=gate_data['name'],
                        description=gate_data['description'],
                        type=gate_data['type'],
                        level_requirement=gate_data['level_requirement'],
                        rank_requirement=gate_data['rank_requirement'],
                        monster_level=gate_data['monster_level'],
                        monster_rank=gate_data['monster_rank'],
                        rewards=gate_data['rewards']
                    )
                    db.session.add(gate)

                db.session.commit()
                print("Test data created successfully")
                return True
            
        except SQLAlchemyError as e:
            print(f"Error creating test data: {e}")
            db.session.rollback()
            return False

    def verify_database(self) -> bool:
        """Verify database setup"""
        try:
            with self.app.app_context():
                # Check tables
                tables = db.engine.table_names()
                expected_tables = [
                    'users', 'player_characters', 'player_skills',
                    'wallets', 'items', 'inventories', 'inventory_items',
                    'guilds', 'guild_member_details', 'parties',
                    'party_member_details', 'party_invitations',
                    'gates', 'gate_sessions', 'magic_beasts',
                    'achievements', 'ai_behaviors', 'transactions',
                    'chat_messages'
                ]
                
                for table in expected_tables:
                    if table not in tables:
                        print(f"Table '{table}' not found")
                        return False
                
                # Check admin user
                admin = db.session.query(User).filter_by(
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
                "admin@terminusa.online",
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
