import unittest
from unittest.mock import Mock, patch
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
import subprocess

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from db_setup import db, init_db
from models import User, Wallet, Gate, Guild
from game_manager import MainGameManager

class TestInitialization(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, '.env')
        self.db_file = os.path.join(self.temp_dir, 'test.db')
        
        # Create test environment file
        with open(self.env_file, 'w') as f:
            f.write("""
FLASK_ENV=testing
TESTING=True
DATABASE_URL=sqlite:///{}
FLASK_SECRET_KEY=test-secret-key
JWT_SECRET_KEY=test-jwt-secret
SOLANA_RPC_URL=https://api.devnet.solana.com
SERVER_PORT=5000
WEBAPP_PORT=5001
""".format(self.db_file))

    def tearDown(self):
        """Clean up after each test"""
        shutil.rmtree(self.temp_dir)

    def test_environment_setup(self):
        """Test environment configuration loading"""
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv(self.env_file)
        
        # Verify environment variables
        self.assertEqual(os.getenv('FLASK_ENV'), 'testing')
        self.assertEqual(os.getenv('DATABASE_URL'), f'sqlite:///{self.db_file}')
        self.assertIsNotNone(os.getenv('FLASK_SECRET_KEY'))
        self.assertIsNotNone(os.getenv('JWT_SECRET_KEY'))

    def test_database_initialization(self):
        """Test database initialization"""
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_file}'
        
        with app.app_context():
            # Initialize database
            init_db(app)
            
            # Verify tables were created
            tables = db.engine.table_names()
            expected_tables = [
                'users',
                'wallets',
                'gates',
                'guilds',
                'items',
                'inventories'
            ]
            
            for table in expected_tables:
                self.assertIn(table.lower(), [t.lower() for t in tables])

    def test_directory_structure(self):
        """Test required directory structure creation"""
        required_dirs = [
            'logs',
            'static',
            'static/images',
            'static/css',
            'static/js',
            'templates'
        ]
        
        for directory in required_dirs:
            path = os.path.join(self.temp_dir, directory)
            os.makedirs(path)
            self.assertTrue(os.path.exists(path))
            self.assertTrue(os.path.isdir(path))

    @patch('subprocess.check_call')
    def test_dependency_installation(self, mock_check_call):
        """Test dependency installation process"""
        # Create requirements file
        requirements = [
            'flask==2.0.1',
            'flask-sqlalchemy==2.5.1',
            'flask-jwt-extended==4.3.1',
            'solders~=0.2.0',
            'solana~=0.25.0'
        ]
        
        req_file = os.path.join(self.temp_dir, 'requirements.txt')
        with open(req_file, 'w') as f:
            f.write('\n'.join(requirements))
        
        # Test installation
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', req_file])
        
        # Verify calls
        mock_check_call.assert_called()

    def test_initial_data_setup(self):
        """Test initial game data setup"""
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_file}'
        
        with app.app_context():
            init_db(app)
            
            # Create admin user
            admin = User(
                username='adminbb',
                password='hashed_password',
                salt='admin_salt',
                role='admin'
            )
            db.session.add(admin)
            
            # Create initial gates
            gates = [
                Gate(
                    name=f'Gate {grade}',
                    grade=grade,
                    min_level=level,
                    max_players=10,
                    crystal_reward=reward
                )
                for grade, level, reward in [
                    ('E', 1, 100),
                    ('D', 10, 200),
                    ('C', 20, 300)
                ]
            ]
            for gate in gates:
                db.session.add(gate)
            
            db.session.commit()
            
            # Verify initial data
            self.assertEqual(User.query.filter_by(role='admin').count(), 1)
            self.assertEqual(Gate.query.count(), 3)

    def test_configuration_validation(self):
        """Test configuration validation"""
        def validate_config(config):
            required_keys = [
                'FLASK_SECRET_KEY',
                'JWT_SECRET_KEY',
                'DATABASE_URL',
                'SOLANA_RPC_URL',
                'SERVER_PORT',
                'WEBAPP_PORT'
            ]
            
            return all(key in config for key in required_keys)
        
        # Test valid configuration
        valid_config = {
            'FLASK_SECRET_KEY': 'secret',
            'JWT_SECRET_KEY': 'jwt-secret',
            'DATABASE_URL': 'sqlite:///test.db',
            'SOLANA_RPC_URL': 'https://api.devnet.solana.com',
            'SERVER_PORT': '5000',
            'WEBAPP_PORT': '5001'
        }
        self.assertTrue(validate_config(valid_config))
        
        # Test invalid configuration
        invalid_config = valid_config.copy()
        del invalid_config['JWT_SECRET_KEY']
        self.assertFalse(validate_config(invalid_config))

    def test_game_system_initialization(self):
        """Test game systems initialization"""
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_file}'
        
        with app.app_context():
            init_db(app)
            
            # Initialize game manager
            game_manager = MainGameManager()
            
            # Verify system initialization
            self.assertIsNotNone(game_manager.game_systems)
            self.assertIsNotNone(game_manager.game_state)
            
            # Test system connections
            self.assertEqual(
                game_manager.game_systems.currency_system,
                game_manager.game_systems.marketplace_system.currency_system
            )

    def test_static_file_setup(self):
        """Test static file setup"""
        static_files = {
            'css': ['style.css'],
            'js': ['main.js'],
            'images': ['logo.png']
        }
        
        for directory, files in static_files.items():
            dir_path = os.path.join(self.temp_dir, 'static', directory)
            os.makedirs(dir_path, exist_ok=True)
            
            for file in files:
                file_path = os.path.join(dir_path, file)
                with open(file_path, 'w') as f:
                    f.write('// Test content')
                
                self.assertTrue(os.path.exists(file_path))

    def test_logging_setup(self):
        """Test logging configuration"""
        import logging
        
        # Create log directory
        log_dir = os.path.join(self.temp_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        log_file = os.path.join(log_dir, 'test.log')
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Test logging
        logger = logging.getLogger('test')
        logger.info('Test log message')
        
        # Verify log file
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn('Test log message', content)

    def test_template_setup(self):
        """Test template setup"""
        template_files = [
            'base.html',
            'index.html',
            'play.html',
            'marketplace.html',
            'guilds.html'
        ]
        
        template_dir = os.path.join(self.temp_dir, 'templates')
        os.makedirs(template_dir, exist_ok=True)
        
        for template in template_files:
            file_path = os.path.join(template_dir, template)
            with open(file_path, 'w') as f:
                f.write('{% extends "base.html" %}')
            
            self.assertTrue(os.path.exists(file_path))

    def test_server_startup(self):
        """Test server startup process"""
        with patch('flask.Flask.run') as mock_run:
            app.config['TESTING'] = True
            port = int(os.getenv('SERVER_PORT', 5000))
            
            # Start server
            app.run(host='0.0.0.0', port=port)
            
            # Verify server startup
            mock_run.assert_called_once_with(
                host='0.0.0.0',
                port=port
            )

if __name__ == '__main__':
    unittest.main()
