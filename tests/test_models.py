import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from db_setup import db
from models import (
    User, Wallet, Inventory, InventoryItem, Item, Gate, MagicBeast,
    Guild, GuildMember, Achievement, AIBehavior, Party, PartyMember,
    PartyInvitation, GateSession
)

class TestModels(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.user = User(
                username='test_user',
                password='hashed_password',
                salt='test_salt',
                role='user',
                level=1,
                job_class='Fighter',
                hp=100,
                mp=100,
                strength=10,
                agility=10,
                intelligence=10,
                luck=10
            )
            db.session.add(self.user)
            db.session.commit()
            
            # Create test wallet
            self.wallet = Wallet(
                user_id=self.user.id,
                address='test_address',
                encrypted_privkey='test_key',
                iv='test_iv',
                sol_balance=Decimal('1.0'),
                crystals=1000,
                exons=1000
            )
            db.session.add(self.wallet)
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_model(self):
        """Test User model relationships and constraints"""
        with self.app.app_context():
            # Test unique username constraint
            duplicate_user = User(
                username='test_user',
                password='other_password',
                salt='other_salt',
                role='user'
            )
            db.session.add(duplicate_user)
            with self.assertRaises(Exception):
                db.session.commit()
            db.session.rollback()
            
            # Test wallet relationship
            user = User.query.get(self.user.id)
            self.assertIsNotNone(user.wallet)
            self.assertEqual(user.wallet.address, 'test_address')
            
            # Test inventory relationship
            inventory = Inventory(user_id=user.id, slots=10)
            db.session.add(inventory)
            db.session.commit()
            
            user = User.query.get(self.user.id)
            self.assertIsNotNone(user.inventory)
            self.assertEqual(user.inventory.slots, 10)

    def test_wallet_model(self):
        """Test Wallet model functionality"""
        with self.app.app_context():
            wallet = Wallet.query.filter_by(user_id=self.user.id).first()
            
            # Test balance updates
            initial_sol = wallet.sol_balance
            wallet.sol_balance += Decimal('0.5')
            db.session.commit()
            
            updated_wallet = Wallet.query.get(wallet.id)
            self.assertEqual(updated_wallet.sol_balance, initial_sol + Decimal('0.5'))
            
            # Test currency constraints
            with self.assertRaises(Exception):
                wallet.sol_balance = -1
                db.session.commit()
            db.session.rollback()

    def test_inventory_system(self):
        """Test inventory and item relationships"""
        with self.app.app_context():
            # Create inventory
            inventory = Inventory(user_id=self.user.id, slots=10)
            db.session.add(inventory)
            
            # Create items
            items = [
                Item(
                    name=f'Test Item {i}',
                    type='weapon',
                    grade='basic',
                    price_exons=100,
                    price_crystals=100,
                    stats={'attack': 10}
                )
                for i in range(3)
            ]
            for item in items:
                db.session.add(item)
            
            db.session.commit()
            
            # Add items to inventory
            for item in items:
                inventory_item = InventoryItem(
                    inventory_id=inventory.id,
                    item_id=item.id,
                    quantity=1
                )
                db.session.add(inventory_item)
            
            db.session.commit()
            
            # Test inventory constraints
            inventory = Inventory.query.get(inventory.id)
            self.assertEqual(len(inventory.items), 3)
            
            # Test inventory slot limit
            for _ in range(8):  # Would exceed 10 slots
                inventory_item = InventoryItem(
                    inventory_id=inventory.id,
                    item_id=items[0].id,
                    quantity=1
                )
                db.session.add(inventory_item)
                
            with self.assertRaises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_gate_system(self):
        """Test gate and magic beast relationships"""
        with self.app.app_context():
            # Create gate
            gate = Gate(
                name='Test Gate',
                grade='E',
                min_level=1,
                max_players=10,
                crystal_reward=100
            )
            db.session.add(gate)
            
            # Create magic beasts
            beasts = [
                MagicBeast(
                    name=f'Beast {i}',
                    type='normal',
                    level=1,
                    stats={'hp': 100, 'damage': 10}
                )
                for i in range(3)
            ]
            for beast in beasts:
                db.session.add(beast)
                
            db.session.commit()
            
            # Create gate session
            session = GateSession(
                gate_id=gate.id,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(minutes=30)
            )
            db.session.add(session)
            db.session.commit()
            
            # Test relationships
            gate = Gate.query.get(gate.id)
            self.assertIsNotNone(gate.sessions)
            self.assertEqual(len(gate.sessions), 1)

    def test_guild_system(self):
        """Test guild relationships and hierarchy"""
        with self.app.app_context():
            # Create guild
            guild = Guild(
                name='Test Guild',
                leader_id=self.user.id,
                level=1,
                exons_balance=0,
                crystals_balance=0
            )
            db.session.add(guild)
            db.session.commit()
            
            # Add members
            members = []
            for i in range(3):
                user = User(
                    username=f'member_{i}',
                    password='hashed_password',
                    salt='test_salt',
                    role='user'
                )
                db.session.add(user)
                db.session.commit()
                
                member = GuildMember(
                    guild_id=guild.id,
                    user_id=user.id,
                    role='member'
                )
                db.session.add(member)
                members.append(member)
            
            db.session.commit()
            
            # Test guild relationships
            guild = Guild.query.get(guild.id)
            self.assertEqual(len(guild.members), 4)  # Including leader
            self.assertEqual(guild.leader_id, self.user.id)
            
            # Test member roles
            leader_member = GuildMember.query.filter_by(
                guild_id=guild.id,
                user_id=self.user.id
            ).first()
            self.assertEqual(leader_member.role, 'leader')

    def test_party_system(self):
        """Test party relationships and invitations"""
        with self.app.app_context():
            # Create party
            party = Party(
                name='Test Party',
                leader_id=self.user.id
            )
            db.session.add(party)
            db.session.commit()
            
            # Add party leader as member
            leader_member = PartyMember(
                party_id=party.id,
                user_id=self.user.id
            )
            db.session.add(leader_member)
            
            # Create and invite members
            for i in range(2):
                user = User(
                    username=f'party_member_{i}',
                    password='hashed_password',
                    salt='test_salt',
                    role='user'
                )
                db.session.add(user)
                db.session.commit()
                
                invitation = PartyInvitation(
                    party_id=party.id,
                    user_id=user.id,
                    expiry=datetime.utcnow() + timedelta(hours=1)
                )
                db.session.add(invitation)
            
            db.session.commit()
            
            # Test party relationships
            party = Party.query.get(party.id)
            self.assertEqual(len(party.members), 1)  # Just the leader
            self.assertEqual(len(party.invitations), 2)
            
            # Test invitation expiry
            expired_invitation = party.invitations[0]
            expired_invitation.expiry = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            
            self.assertTrue(expired_invitation.is_expired())

    def test_achievement_system(self):
        """Test achievement tracking"""
        with self.app.app_context():
            # Create achievement
            achievement = Achievement(
                name='First Gate',
                description='Clear your first gate',
                requirements={'gates_cleared': 1},
                reward_crystals=100,
                bonus_stats={'strength': 1}
            )
            db.session.add(achievement)
            db.session.commit()
            
            # Track user achievement
            self.user.completed_achievements.append(achievement)
            db.session.commit()
            
            # Test achievement tracking
            user = User.query.get(self.user.id)
            self.assertEqual(len(user.completed_achievements), 1)
            self.assertEqual(
                user.completed_achievements[0].name,
                'First Gate'
            )

    def test_ai_behavior(self):
        """Test AI behavior tracking"""
        with self.app.app_context():
            # Create AI behavior record
            behavior = AIBehavior(
                user_id=self.user.id,
                activity_history=[
                    {
                        'type': 'gate_hunting',
                        'success': True,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                ],
                preferences={
                    'combat': 0.8,
                    'economy': 0.2
                }
            )
            db.session.add(behavior)
            db.session.commit()
            
            # Test behavior tracking
            behavior = AIBehavior.query.filter_by(
                user_id=self.user.id
            ).first()
            self.assertIsNotNone(behavior)
            self.assertEqual(len(behavior.activity_history), 1)
            self.assertEqual(behavior.preferences['combat'], 0.8)

if __name__ == '__main__':
    unittest.main()
