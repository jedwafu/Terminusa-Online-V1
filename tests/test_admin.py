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
from models import User, Wallet, Gate, Guild, Item
from admin_dashboard import AdminDashboard

class TestAdminFunctionality(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        
        with self.app.app_context():
            db.create_all()
            
            # Create admin user
            self.admin = User(
                username='adminbb',
                password='hashed_admin_password',
                salt='admin_salt',
                role='admin',
                level=999,
                job_class='Administrator'
            )
            db.session.add(self.admin)
            
            # Create admin wallet
            self.admin_wallet = Wallet(
                user_id=self.admin.id,
                address='FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw',
                encrypted_privkey='admin_key',
                iv='admin_iv',
                sol_balance=Decimal('1000.0'),
                crystals=1000000,
                exons=1000000
            )
            db.session.add(self.admin_wallet)
            
            # Create test users
            self.test_users = []
            for i in range(3):
                user = User(
                    username=f'test_user_{i}',
                    password='hashed_password',
                    salt='test_salt',
                    role='user',
                    level=1
                )
                db.session.add(user)
                self.test_users.append(user)
            
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_management(self):
        """Test user management capabilities"""
        with self.app.app_context():
            admin_dashboard = AdminDashboard(self.admin)
            
            # Test user listing
            users = admin_dashboard.list_users()
            self.assertEqual(len(users), 4)  # Admin + 3 test users
            
            # Test user update
            update_data = {
                'level': 10,
                'job_class': 'Fighter',
                'role': 'user'
            }
            result = admin_dashboard.update_user(self.test_users[0].id, update_data)
            self.assertEqual(result['status'], 'success')
            
            updated_user = User.query.get(self.test_users[0].id)
            self.assertEqual(updated_user.level, 10)
            
            # Test user deletion
            result = admin_dashboard.delete_user(self.test_users[1].id)
            self.assertEqual(result['status'], 'success')
            
            # Verify deletion
            deleted_user = User.query.get(self.test_users[1].id)
            self.assertIsNone(deleted_user)

    def test_currency_management(self):
        """Test currency system management"""
        with self.app.app_context():
            admin_dashboard = AdminDashboard(self.admin)
            
            # Test currency supply adjustment
            result = admin_dashboard.adjust_currency_supply(
                'CRYSTAL',
                amount=1000000,
                operation='mint'
            )
            self.assertEqual(result['status'], 'success')
            
            # Test tax rate adjustment
            result = admin_dashboard.update_tax_rates({
                'marketplace': 0.15,  # 15%
                'guild': 0.03        # 3%
            })
            self.assertEqual(result['status'], 'success')
            
            # Test admin wallet operations
            result = admin_dashboard.transfer_admin_funds(
                currency='EXON',
                amount=1000,
                to_address='recipient_address'
            )
            self.assertEqual(result['status'], 'success')

    def test_game_configuration(self):
        """Test game configuration management"""
        with self.app.app_context():
            admin_dashboard = AdminDashboard(self.admin)
            
            # Test gate configuration
            gate_config = {
                'grade': 'S',
                'min_level': 70,
                'max_players': 10,
                'crystal_reward': 1000
            }
            result = admin_dashboard.create_gate(gate_config)
            self.assertEqual(result['status'], 'success')
            
            # Test item creation
            item_config = {
                'name': 'Admin Sword',
                'type': 'weapon',
                'grade': 'legendary',
                'price_exons': 10000,
                'price_crystals': 10000,
                'stats': {'attack': 100}
            }
            result = admin_dashboard.create_item(item_config)
            self.assertEqual(result['status'], 'success')
            
            # Test game parameters
            params = {
                'max_party_size': 8,
                'max_guild_size': 100,
                'base_gate_reward': 50
            }
            result = admin_dashboard.update_game_parameters(params)
            self.assertEqual(result['status'], 'success')

    def test_monitoring_tools(self):
        """Test monitoring and analytics tools"""
        with self.app.app_context():
            admin_dashboard = AdminDashboard(self.admin)
            
            # Test user activity monitoring
            activity_data = admin_dashboard.get_user_activity_stats(
                timeframe='24h'
            )
            self.assertIn('active_users', activity_data)
            self.assertIn('new_registrations', activity_data)
            
            # Test economy monitoring
            economy_stats = admin_dashboard.get_economy_stats()
            self.assertIn('total_crystal_supply', economy_stats)
            self.assertIn('total_exon_supply', economy_stats)
            self.assertIn('marketplace_volume', economy_stats)
            
            # Test system performance
            performance_data = admin_dashboard.get_system_performance()
            self.assertIn('cpu_usage', performance_data)
            self.assertIn('memory_usage', performance_data)
            self.assertIn('active_connections', performance_data)

    def test_moderation_tools(self):
        """Test moderation capabilities"""
        with self.app.app_context():
            admin_dashboard = AdminDashboard(self.admin)
            
            # Test user ban
            result = admin_dashboard.ban_user(
                self.test_users[0].id,
                reason="Terms of Service violation",
                duration_days=30
            )
            self.assertEqual(result['status'], 'success')
            
            # Test chat moderation
            result = admin_dashboard.moderate_chat_message(
                message_id=1,
                action='delete',
                reason='Inappropriate content'
            )
            self.assertEqual(result['status'], 'success')
            
            # Test guild moderation
            result = admin_dashboard.moderate_guild(
                guild_id=1,
                action='warning',
                reason='Inappropriate guild name'
            )
            self.assertEqual(result['status'], 'success')

    def test_backup_restore(self):
        """Test backup and restore functionality"""
        with self.app.app_context():
            admin_dashboard = AdminDashboard(self.admin)
            
            # Test database backup
            backup_result = admin_dashboard.create_backup(
                backup_type='full',
                description='Test backup'
            )
            self.assertEqual(backup_result['status'], 'success')
            self.assertIn('backup_id', backup_result)
            
            # Test backup restoration
            restore_result = admin_dashboard.restore_backup(
                backup_id=backup_result['backup_id']
            )
            self.assertEqual(restore_result['status'], 'success')

    def test_admin_logs(self):
        """Test administrative action logging"""
        with self.app.app_context():
            admin_dashboard = AdminDashboard(self.admin)
            
            # Perform some admin actions
            admin_dashboard.update_user(
                self.test_users[0].id,
                {'level': 20}
            )
            
            admin_dashboard.adjust_currency_supply(
                'CRYSTAL',
                amount=1000,
                operation='mint'
            )
            
            # Check admin logs
            logs = admin_dashboard.get_admin_logs(
                timeframe='1h',
                action_type='all'
            )
            
            self.assertGreater(len(logs), 0)
            self.assertEqual(logs[0]['admin_id'], self.admin.id)
            self.assertIn('action', logs[0])
            self.assertIn('timestamp', logs[0])

    def test_security_controls(self):
        """Test admin security controls"""
        with self.app.app_context():
            admin_dashboard = AdminDashboard(self.admin)
            
            # Test role elevation prevention
            result = admin_dashboard.update_user(
                self.test_users[0].id,
                {'role': 'admin'}  # Attempt to elevate to admin
            )
            self.assertEqual(result['status'], 'error')
            
            # Test critical action confirmation
            with self.assertRaises(Exception):
                admin_dashboard.delete_user(
                    self.test_users[0].id,
                    confirmation=False
                )
            
            # Test admin action rate limiting
            for _ in range(100):  # Exceed rate limit
                admin_dashboard.get_admin_logs(timeframe='1h')
            
            result = admin_dashboard.get_admin_logs(timeframe='1h')
            self.assertEqual(result['status'], 'error')
            self.assertIn('rate_limit_exceeded', result['message'])

if __name__ == '__main__':
    unittest.main()
