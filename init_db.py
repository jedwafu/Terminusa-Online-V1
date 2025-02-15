#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import (
    Base, User, UserRole, Item, ItemType, ItemRarity,
    Guild, Party, Achievement, Gate, GateType,
    MagicBeast, AIBehavior, Transaction, MarketListing,
    ChatMessage, UserSession, AuditLog, SystemMetric,
    GameEvent
)
import json
import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('.env.test', override=True)

class DatabaseInitializer:
    """Initialize database with initial data"""
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv('DB_URL', 'sqlite:///terminusa.db')
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)

    def init_database(self) -> bool:
        """Initialize database schema and data"""
        try:
            print("Initializing database...")
            
            # Create tables
            Base.metadata.create_all(self.engine)
            
            # Create initial data
            session = self.Session()
            
            try:
                # Create admin user
                self._create_admin_user(session)
                
                # Create test users
                self._create_test_users(session)
                
                # Create items
                self._create_items(session)
                
                # Create achievements
                self._create_achievements(session)
                
                # Create gates
                self._create_gates(session)
                
                # Create magic beasts
                self._create_magic_beasts(session)
                
                # Create AI behaviors
                self._create_ai_behaviors(session)
                
                # Create game events
                self._create_game_events(session)
                
                session.commit()
                print("Database initialized successfully!")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"Error initializing database: {e}")
                return False
                
            finally:
                session.close()
                
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False

    def _create_admin_user(self, session):
        """Create admin user"""
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(
            admin_password.encode('utf-8'),
            salt
        ).decode('utf-8')
        
        admin = User(
            username='admin',
            email='admin@terminusa.com',
            password_hash=password_hash,
            role=UserRole.ADMIN,
            level=100,
            experience=1000000,
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
        print("Admin user created")

    def _create_test_users(self, session):
        """Create test users"""
        for i in range(1, 6):
            password = f"password{i}"
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                salt
            ).decode('utf-8')
            
            user = User(
                username=f"test_user_{i}",
                email=f"test{i}@example.com",
                password_hash=password_hash,
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
            
            session.add(user)
        print("Test users created")

    def _create_items(self, session):
        """Create game items"""
        items = [
            {
                'name': 'Iron Sword',
                'description': 'A basic iron sword',
                'type': ItemType.WEAPON,
                'rarity': ItemRarity.COMMON,
                'level_requirement': 1,
                'stats': {'damage': 10, 'speed': 5},
                'tradeable': True
            },
            {
                'name': 'Steel Armor',
                'description': 'Sturdy steel armor',
                'type': ItemType.ARMOR,
                'rarity': ItemRarity.UNCOMMON,
                'level_requirement': 10,
                'stats': {'defense': 20, 'weight': 15},
                'tradeable': True
            },
            {
                'name': 'Health Potion',
                'description': 'Restores 100 HP',
                'type': ItemType.CONSUMABLE,
                'rarity': ItemRarity.COMMON,
                'level_requirement': 1,
                'stats': {'heal': 100},
                'tradeable': True,
                'stackable': True,
                'max_stack': 99
            }
        ]
        
        for item_data in items:
            item = Item(**item_data)
            session.add(item)
        print("Items created")

    def _create_achievements(self, session):
        """Create achievements"""
        achievements = [
            {
                'name': 'First Steps',
                'description': 'Reach level 10',
                'requirements': {'level': 10},
                'rewards': {'crystals': 100, 'title': 'Novice'}
            },
            {
                'name': 'Monster Hunter',
                'description': 'Defeat 100 monsters',
                'requirements': {'monsters_defeated': 100},
                'rewards': {'gold': 1000, 'title': 'Hunter'}
            },
            {
                'name': 'Wealthy',
                'description': 'Accumulate 10000 gold',
                'requirements': {'gold': 10000},
                'rewards': {'crystals': 500, 'title': 'Merchant'}
            }
        ]
        
        for achievement_data in achievements:
            achievement = Achievement(**achievement_data)
            session.add(achievement)
        print("Achievements created")

    def _create_gates(self, session):
        """Create gates"""
        gates = [
            {
                'name': 'Forest Gate',
                'description': 'A mysterious gate in the forest',
                'type': GateType.NORMAL,
                'level_requirement': 1,
                'min_players': 1,
                'max_players': 4,
                'rewards': {
                    'experience': 100,
                    'gold': 50,
                    'items': {'health_potion': 0.5}
                }
            },
            {
                'name': 'Dragon\'s Lair',
                'description': 'Home of the ancient dragon',
                'type': GateType.BOSS,
                'level_requirement': 50,
                'min_players': 4,
                'max_players': 8,
                'rewards': {
                    'experience': 1000,
                    'gold': 5000,
                    'items': {'dragon_scale': 1.0}
                }
            }
        ]
        
        for gate_data in gates:
            gate = Gate(**gate_data)
            session.add(gate)
        print("Gates created")

    def _create_magic_beasts(self, session):
        """Create magic beasts"""
        beasts = [
            {
                'name': 'Forest Wolf',
                'description': 'A common wolf of the forest',
                'level': 5,
                'stats': {
                    'health': 100,
                    'attack': 15,
                    'defense': 10
                },
                'abilities': ['bite', 'howl'],
                'drops': {'wolf_fang': 0.3, 'wolf_pelt': 0.5}
            },
            {
                'name': 'Ancient Dragon',
                'description': 'A powerful dragon',
                'level': 50,
                'stats': {
                    'health': 10000,
                    'attack': 500,
                    'defense': 300
                },
                'abilities': ['flame_breath', 'tail_swipe'],
                'drops': {'dragon_scale': 1.0, 'dragon_heart': 0.1}
            }
        ]
        
        for beast_data in beasts:
            beast = MagicBeast(**beast_data)
            session.add(beast)
        print("Magic beasts created")

    def _create_ai_behaviors(self, session):
        """Create AI behaviors"""
        behaviors = [
            {
                'name': 'Aggressive',
                'description': 'Attacks players on sight',
                'conditions': {'health_threshold': 0.3},
                'actions': ['chase', 'attack'],
                'priorities': {'attack': 1, 'chase': 2}
            },
            {
                'name': 'Defensive',
                'description': 'Defends territory',
                'conditions': {'in_territory': True},
                'actions': ['patrol', 'attack'],
                'priorities': {'defend': 1, 'patrol': 2}
            }
        ]
        
        for behavior_data in behaviors:
            behavior = AIBehavior(**behavior_data)
            session.add(behavior)
        print("AI behaviors created")

    def _create_game_events(self, session):
        """Create game events"""
        now = datetime.utcnow()
        events = [
            {
                'name': 'Double XP Weekend',
                'description': 'Earn double experience',
                'start_time': now + timedelta(days=1),
                'end_time': now + timedelta(days=3),
                'rewards': {'experience_multiplier': 2.0},
                'requirements': {'level': 1}
            },
            {
                'name': 'Boss Rush',
                'description': 'Special boss event',
                'start_time': now + timedelta(days=7),
                'end_time': now + timedelta(days=8),
                'rewards': {'boss_drops': 2.0},
                'requirements': {'level': 30}
            }
        ]
        
        for event_data in events:
            event = GameEvent(**event_data)
            session.add(event)
        print("Game events created")

def main():
    """Main entry point"""
    print("Initializing Terminusa Online database...")
    
    # Get database URL from environment
    db_url = os.getenv('DB_URL')
    if not db_url:
        print("Error: DB_URL environment variable not set")
        return 1
    
    # Initialize database
    initializer = DatabaseInitializer(db_url)
    if not initializer.init_database():
        return 1
    
    print("\nDatabase initialization completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
