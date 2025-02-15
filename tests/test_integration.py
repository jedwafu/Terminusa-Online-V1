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
    User, Wallet, Inventory, Item, Gate, Guild, Party,
    GuildMember, PartyMember
)
from game_systems import GameManager
from economy_systems import CurrencySystem
from ai_manager import AISystem

class TestSystemIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        
        with self.app.app_context():
            db.create_all()
            
            # Initialize game systems
            self.game_manager = GameManager()
            self.currency_system = CurrencySystem()
            self.ai_system = AISystem()
            
            # Create test user
            self.user = User(
                username='test_user',
                password='hashed_password',
                salt='test_salt',
                role='user',
                level=10,
                job_class='Fighter',
                hp=1000,
                mp=500,
                strength=50,
                agility=30,
                intelligence=40,
                luck=20
            )
            db.session.add(self.user)
            
            # Create wallet
            self.wallet = Wallet(
                user_id=1,
                address='test_address',
                encrypted_privkey='test_key',
                iv='test_iv',
                sol_balance=Decimal('1.0'),
                crystals=1000,
                exons=1000
            )
            db.session.add(self.wallet)
            
            # Create inventory
            self.inventory = Inventory(user_id=1, slots=10)
            db.session.add(self.inventory)
            
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_gate_completion_flow(self):
        """Test complete gate completion flow"""
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
            db.session.commit()
            
            # Enter gate
            result = self.game_manager.process_command(
                'gate_enter',
                self.user.id,
                {'gate_id': gate.id}
            )
            self.assertEqual(result['status'], 'success')
            
            # Complete gate
            result = self.game_manager.process_command(
                'gate_complete',
                self.user.id,
                {'gate_id': gate.id}
            )
            self.assertEqual(result['status'], 'success')
            
            # Verify rewards
            wallet = Wallet.query.get(self.wallet.id)
            self.assertGreater(wallet.crystals, 1000)  # Initial amount
            
            # Verify experience gain
            user = User.query.get(self.user.id)
            self.assertGreater(user.experience, 0)
            
            # Verify AI behavior tracking
            behavior = self.ai_system.analyze_player_behavior(
                self.user.id,
                [{'type': 'gate_hunting', 'success': True}]
            )
            self.assertGreater(behavior.success_rates['gate_hunting'], 0)

    def test_marketplace_transaction_flow(self):
        """Test complete marketplace transaction flow"""
        with self.app.app_context():
            # Create item
            item = Item(
                name='Test Sword',
                type='weapon',
                grade='basic',
                price_exons=100,
                price_crystals=100,
                stats={'attack': 10}
            )
            db.session.add(item)
            db.session.commit()
            
            # Create listing
            result = self.game_manager.process_command(
                'marketplace_create',
                self.user.id,
                {
                    'item_id': item.id,
                    'price': 100,
                    'currency': 'CRYSTAL'
                }
            )
            self.assertEqual(result['status'], 'success')
            
            # Create buyer
            buyer = User(
                username='buyer',
                password='hashed_password',
                salt='test_salt',
                role='user'
            )
            db.session.add(buyer)
            
            buyer_wallet = Wallet(
                user_id=buyer.id,
                address='buyer_address',
                encrypted_privkey='buyer_key',
                iv='buyer_iv',
                sol_balance=Decimal('1.0'),
                crystals=1000,
                exons=1000
            )
            db.session.add(buyer_wallet)
            db.session.commit()
            
            # Purchase item
            result = self.game_manager.process_command(
                'marketplace_purchase',
                buyer.id,
                {'listing_id': result['listing_id']}
            )
            self.assertEqual(result['status'], 'success')
            
            # Verify currency transfer
            seller_wallet = Wallet.query.get(self.wallet.id)
            buyer_wallet = Wallet.query.get(buyer_wallet.id)
            
            self.assertGreater(seller_wallet.crystals, 1000)  # Initial + sale
            self.assertLess(buyer_wallet.crystals, 1000)      # Initial - purchase

    def test_guild_party_interaction(self):
        """Test guild and party system interaction"""
        with self.app.app_context():
            # Create guild
            result = self.game_manager.process_command(
                'guild_create',
                self.user.id,
                {'name': "Test Guild"}
            )
            self.assertEqual(result['status'], 'success')
            guild_id = result['guild_id']
            
            # Create party members (guild mates)
            members = []
            for i in range(3):
                member = User(
                    username=f'member_{i}',
                    password='hashed_password',
                    salt='test_salt',
                    role='user',
                    level=10
                )
                db.session.add(member)
                db.session.commit()
                
                # Add to guild
                guild_member = GuildMember(
                    guild_id=guild_id,
                    user_id=member.id,
                    role='member'
                )
                db.session.add(guild_member)
                members.append(member)
            
            db.session.commit()
            
            # Create party with guild members
            result = self.game_manager.process_command(
                'party_create',
                self.user.id,
                {'name': "Guild Party"}
            )
            self.assertEqual(result['status'], 'success')
            party_id = result['party_id']
            
            # Add guild members to party
            for member in members:
                result = self.game_manager.process_command(
                    'party_invite',
                    self.user.id,
                    {
                        'party_id': party_id,
                        'user_id': member.id
                    }
                )
                self.assertEqual(result['status'], 'success')
            
            # Enter gate as guild party
            gate = Gate(
                name='Guild Gate',
                grade='E',
                min_level=1,
                max_players=10,
                crystal_reward=100
            )
            db.session.add(gate)
            db.session.commit()
            
            result = self.game_manager.process_command(
                'gate_enter',
                self.user.id,
                {
                    'gate_id': gate.id,
                    'party_id': party_id
                }
            )
            self.assertEqual(result['status'], 'success')
            
            # Complete gate
            result = self.game_manager.process_command(
                'gate_complete',
                self.user.id,
                {
                    'gate_id': gate.id,
                    'party_id': party_id
                }
            )
            self.assertEqual(result['status'], 'success')
            
            # Verify guild rewards
            guild = Guild.query.get(guild_id)
            self.assertGreater(guild.crystals_balance, 0)

    def test_ai_economy_integration(self):
        """Test AI system integration with economy"""
        with self.app.app_context():
            # Create activity history
            activities = [
                {'type': 'trading', 'success': True},
                {'type': 'trading', 'success': True},
                {'type': 'gambling', 'success': False}
            ]
            
            # Get player behavior profile
            profile = self.ai_system.analyze_player_behavior(
                self.user.id,
                activities
            )
            
            # Test gacha rate adjustment
            base_rates = self.game_manager.game_systems.gacha_system.rates
            adjusted_rates = self.ai_system.adjust_gacha_rates(
                profile,
                base_rates
            )
            
            # Verify rates are adjusted based on behavior
            self.assertNotEqual(base_rates, adjusted_rates)
            
            # Test marketplace recommendations
            recommendations = self.game_manager.process_command(
                'marketplace_recommendations',
                self.user.id,
                {'profile': profile}
            )
            self.assertEqual(recommendations['status'], 'success')
            self.assertIn('items', recommendations)

    def test_progression_economy_integration(self):
        """Test progression system integration with economy"""
        with self.app.app_context():
            initial_crystals = self.wallet.crystals
            initial_level = self.user.level
            
            # Complete achievements
            for _ in range(5):
                result = self.game_manager.process_command(
                    'gate_complete',
                    self.user.id,
                    {'gate_id': 1}
                )
                self.assertEqual(result['status'], 'success')
            
            # Verify progression rewards
            user = User.query.get(self.user.id)
            wallet = Wallet.query.get(self.wallet.id)
            
            self.assertGreater(user.level, initial_level)
            self.assertGreater(wallet.crystals, initial_crystals)
            
            # Test stat-based pricing
            shop_prices = self.game_manager.process_command(
                'shop_prices',
                self.user.id,
                {}
            )
            self.assertEqual(shop_prices['status'], 'success')
            
            # Higher level should affect certain prices
            self.assertNotEqual(
                shop_prices['prices']['job_reset'],
                100  # Base price
            )

    def test_combat_inventory_integration(self):
        """Test combat system integration with inventory"""
        with self.app.app_context():
            # Add equipment
            weapon = Item(
                name='Test Sword',
                type='weapon',
                grade='basic',
                price_exons=100,
                price_crystals=100,
                stats={'attack': 10}
            )
            db.session.add(weapon)
            db.session.commit()
            
            # Add to inventory
            result = self.game_manager.process_command(
                'inventory_add',
                self.user.id,
                {
                    'item_id': weapon.id,
                    'slot': 0
                }
            )
            self.assertEqual(result['status'], 'success')
            
            # Enter combat with equipment
            result = self.game_manager.process_command(
                'gate_enter',
                self.user.id,
                {'gate_id': 1}
            )
            self.assertEqual(result['status'], 'success')
            
            # Verify equipment effects
            combat_stats = result['combat_results']['player_stats']
            self.assertGreater(combat_stats['attack'], 50)  # Base + weapon
            
            # Verify durability loss
            result = self.game_manager.process_command(
                'inventory_get',
                self.user.id,
                {'slot': 0}
            )
            self.assertLess(
                result['item']['durability'],
                100  # Initial durability
            )

if __name__ == '__main__':
    unittest.main()
