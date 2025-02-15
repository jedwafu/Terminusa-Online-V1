import unittest
from unittest.mock import Mock, patch
import sys
import os
import tempfile
import sqlite3
from datetime import datetime
from pathlib import Path
import alembic
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from db_setup import db
from models import User, Wallet, Gate, Guild

class TestMigrations(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, 'test.db')
        
        # Configure test application
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_file}'
        app.config['TESTING'] = True
        
        # Set up Alembic
        self.alembic_cfg = Config()
        self.alembic_cfg.set_main_option(
            "script_location",
            os.path.join(os.path.dirname(self.temp_dir), "migrations")
        )
        self.alembic_cfg.set_main_option(
            "sqlalchemy.url",
            f'sqlite:///{self.db_file}'
        )

    def tearDown(self):
        """Clean up after each test"""
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        os.rmdir(self.temp_dir)

    def test_initial_migration(self):
        """Test initial database migration"""
        with app.app_context():
            # Create initial schema
            db.create_all()
            
            # Create migration
            self._create_migration("initial")
            
            # Verify migration
            self._verify_schema_version("initial")
            
            # Check tables
            tables = self._get_tables()
            expected_tables = [
                'users',
                'wallets',
                'gates',
                'guilds',
                'items',
                'inventories'
            ]
            
            for table in expected_tables:
                self.assertIn(table, tables)

    def test_add_column_migration(self):
        """Test migration adding new columns"""
        with app.app_context():
            # Create initial schema
            db.create_all()
            
            # Create migration for new column
            self._create_migration("add_user_status")
            
            # Add column to model
            class UserStatus:
                ACTIVE = 'active'
                INACTIVE = 'inactive'
                BANNED = 'banned'
            
            User.status = db.Column(
                db.String(20),
                default=UserStatus.ACTIVE
            )
            
            # Apply migration
            self._apply_migration()
            
            # Verify column
            columns = self._get_columns('users')
            self.assertIn('status', columns)

    def test_modify_column_migration(self):
        """Test migration modifying existing columns"""
        with app.app_context():
            # Create initial schema
            db.create_all()
            
            # Create migration for column modification
            self._create_migration("modify_wallet_balance")
            
            # Modify column in model
            Wallet.sol_balance = db.Column(
                db.Numeric(precision=18, scale=8),
                nullable=False,
                default=0
            )
            
            # Apply migration
            self._apply_migration()
            
            # Verify column type
            column_type = self._get_column_type('wallets', 'sol_balance')
            self.assertIn('NUMERIC', column_type.upper())

    def test_data_migration(self):
        """Test data migration process"""
        with app.app_context():
            # Create initial schema and data
            db.create_all()
            
            # Create test data
            user = User(
                username='test_user',
                password='hashed_password',
                salt='test_salt',
                role='user'
            )
            db.session.add(user)
            db.session.commit()
            
            # Create migration for data transformation
            self._create_migration("transform_user_roles")
            
            # Define data migration
            def upgrade_data():
                """Upgrade user roles"""
                with app.app_context():
                    users = User.query.all()
                    for user in users:
                        if user.role == 'user':
                            user.role = 'player'
                    db.session.commit()
            
            # Apply migration
            self._apply_migration(data_upgrade=upgrade_data)
            
            # Verify data transformation
            user = User.query.first()
            self.assertEqual(user.role, 'player')

    def test_rollback_migration(self):
        """Test migration rollback capabilities"""
        with app.app_context():
            # Create initial schema
            db.create_all()
            
            # Create and apply migration
            self._create_migration("add_test_table")
            self._apply_migration()
            
            # Verify table exists
            tables_before = self._get_tables()
            self.assertIn('test_table', tables_before)
            
            # Rollback migration
            self._rollback_migration()
            
            # Verify table removed
            tables_after = self._get_tables()
            self.assertNotIn('test_table', tables_after)

    def test_dependent_migrations(self):
        """Test migrations with dependencies"""
        with app.app_context():
            # Create initial schema
            db.create_all()
            
            # Create first migration
            self._create_migration("add_guild_type")
            
            # Add column to model
            Guild.type = db.Column(db.String(50))
            
            # Apply first migration
            self._apply_migration()
            
            # Create dependent migration
            self._create_migration("add_guild_features")
            
            # Add dependent column
            Guild.features = db.Column(
                db.JSON,
                nullable=True
            )
            
            # Apply dependent migration
            self._apply_migration()
            
            # Verify both columns
            columns = self._get_columns('guilds')
            self.assertIn('type', columns)
            self.assertIn('features', columns)

    def test_migration_conflicts(self):
        """Test handling of migration conflicts"""
        with app.app_context():
            # Create initial schema
            db.create_all()
            
            # Create conflicting migrations
            self._create_migration("add_user_field_1")
            self._create_migration("add_user_field_2")
            
            # Try to apply conflicting migrations
            with self.assertRaises(Exception):
                self._apply_migration()

    def test_large_data_migration(self):
        """Test migration with large dataset"""
        with app.app_context():
            # Create initial schema
            db.create_all()
            
            # Create large dataset
            users = []
            for i in range(1000):
                user = User(
                    username=f'user_{i}',
                    password='hashed_password',
                    salt='test_salt',
                    role='user'
                )
                users.append(user)
            
            db.session.bulk_save_objects(users)
            db.session.commit()
            
            # Create migration
            self._create_migration("update_large_dataset")
            
            # Define batch processing
            def upgrade_data():
                """Upgrade data in batches"""
                batch_size = 100
                with app.app_context():
                    for offset in range(0, 1000, batch_size):
                        users = User.query.offset(offset).limit(batch_size).all()
                        for user in users:
                            user.role = 'player'
                        db.session.commit()
            
            # Apply migration
            start_time = datetime.now()
            self._apply_migration(data_upgrade=upgrade_data)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Verify performance
            self.assertLess(duration, 5)  # Should complete within 5 seconds

    def _create_migration(self, name: str):
        """Create a new migration"""
        alembic.command.revision(
            self.alembic_cfg,
            message=name,
            autogenerate=True
        )

    def _apply_migration(self, data_upgrade=None):
        """Apply pending migrations"""
        alembic.command.upgrade(self.alembic_cfg, "head")
        if data_upgrade:
            data_upgrade()

    def _rollback_migration(self):
        """Rollback last migration"""
        alembic.command.downgrade(self.alembic_cfg, "-1")

    def _verify_schema_version(self, expected_version: str):
        """Verify current schema version"""
        script = ScriptDirectory.from_config(self.alembic_cfg)
        with EnvironmentContext(
            self.alembic_cfg,
            script
        ) as env:
            current_rev = env.get_current_revision()
            self.assertIsNotNone(current_rev)

    def _get_tables(self) -> list:
        """Get list of database tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables

    def _get_columns(self, table: str) -> list:
        """Get columns for a table"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        return columns

    def _get_column_type(self, table: str, column: str) -> str:
        """Get column type"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        for row in cursor.fetchall():
            if row[1] == column:
                conn.close()
                return row[2]
        conn.close()
        return None

if __name__ == '__main__':
    unittest.main()
