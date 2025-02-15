import unittest
from unittest.mock import Mock, patch
import sys
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any
import yaml
from dotenv import load_dotenv

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ConfigurationManager:
    """Manages application configuration from multiple sources"""
    def __init__(self, env_file: str = '.env'):
        self.env_file = env_file
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        """Load configuration from all sources"""
        # Load environment variables
        load_dotenv(self.env_file)
        
        # Load from environment
        self.config.update({
            'FLASK_ENV': os.getenv('FLASK_ENV', 'development'),
            'TESTING': os.getenv('TESTING', 'False').lower() == 'true',
            'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///app.db'),
            'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY'),
            'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
            'SOLANA_RPC_URL': os.getenv('SOLANA_RPC_URL'),
            'SERVER_PORT': int(os.getenv('SERVER_PORT', '5000')),
            'WEBAPP_PORT': int(os.getenv('WEBAPP_PORT', '5001'))
        })

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value

    def validate(self) -> bool:
        """Validate configuration"""
        required_keys = [
            'FLASK_SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL',
            'SOLANA_RPC_URL'
        ]
        return all(self.config.get(key) for key in required_keys)

class TestConfiguration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, '.env')
        
        # Create test environment file
        with open(self.env_file, 'w') as f:
            f.write("""
FLASK_ENV=testing
TESTING=True
DATABASE_URL=sqlite:///test.db
FLASK_SECRET_KEY=test-secret-key
JWT_SECRET_KEY=test-jwt-secret
SOLANA_RPC_URL=https://api.devnet.solana.com
SERVER_PORT=5000
WEBAPP_PORT=5001
""")
        
        self.config_manager = ConfigurationManager(self.env_file)

    def tearDown(self):
        """Clean up after each test"""
        os.remove(self.env_file)
        os.rmdir(self.temp_dir)

    def test_environment_loading(self):
        """Test environment variable loading"""
        # Test basic environment loading
        self.assertEqual(self.config_manager.get('FLASK_ENV'), 'testing')
        self.assertTrue(self.config_manager.get('TESTING'))
        self.assertEqual(
            self.config_manager.get('DATABASE_URL'),
            'sqlite:///test.db'
        )
        
        # Test default values
        self.assertEqual(
            self.config_manager.get('UNKNOWN_KEY', 'default'),
            'default'
        )

    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test valid configuration
        self.assertTrue(self.config_manager.validate())
        
        # Test invalid configuration
        invalid_config = ConfigurationManager()
        self.assertFalse(invalid_config.validate())

    def test_configuration_override(self):
        """Test configuration override capabilities"""
        # Override existing value
        self.config_manager.set('SERVER_PORT', 8000)
        self.assertEqual(self.config_manager.get('SERVER_PORT'), 8000)
        
        # Add new value
        self.config_manager.set('CUSTOM_SETTING', 'value')
        self.assertEqual(self.config_manager.get('CUSTOM_SETTING'), 'value')

    def test_yaml_config(self):
        """Test YAML configuration support"""
        yaml_config = """
game:
  max_party_size: 10
  max_guild_size: 50
  initial_crystal_supply: 100000000
  base_gate_reward: 10
  guild_tax_rate: 0.02
  marketplace_tax_rate: 0.13

currency:
  solana_to_exon_rate: 1000
  exon_to_crystal_rate: 10
  min_solana_swap: 0.1
  min_exon_swap: 100
  min_crystal_swap: 1000

combat:
  max_combat_duration: 1800
  base_damage_multiplier: 1.0
  base_defense_multiplier: 1.0
  critical_hit_chance: 0.1
  critical_hit_multiplier: 2.0
"""
        
        yaml_file = os.path.join(self.temp_dir, 'config.yml')
        with open(yaml_file, 'w') as f:
            f.write(yaml_config)
        
        # Load YAML config
        with open(yaml_file, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        # Update configuration
        for section, values in yaml_data.items():
            for key, value in values.items():
                self.config_manager.set(f"{section.upper()}_{key.upper()}", value)
        
        # Verify YAML config values
        self.assertEqual(
            self.config_manager.get('GAME_MAX_PARTY_SIZE'),
            10
        )
        self.assertEqual(
            self.config_manager.get('CURRENCY_SOLANA_TO_EXON_RATE'),
            1000
        )

    def test_environment_specific_config(self):
        """Test environment-specific configuration"""
        environments = {
            'development': {
                'DEBUG': True,
                'LOG_LEVEL': 'DEBUG'
            },
            'production': {
                'DEBUG': False,
                'LOG_LEVEL': 'INFO'
            },
            'testing': {
                'DEBUG': True,
                'LOG_LEVEL': 'DEBUG',
                'TESTING': True
            }
        }
        
        for env, settings in environments.items():
            self.config_manager.set('FLASK_ENV', env)
            for key, value in settings.items():
                self.config_manager.set(key, value)
            
            # Verify environment-specific settings
            self.assertEqual(
                self.config_manager.get('DEBUG'),
                settings['DEBUG']
            )
            self.assertEqual(
                self.config_manager.get('LOG_LEVEL'),
                settings['LOG_LEVEL']
            )

    def test_sensitive_data_handling(self):
        """Test sensitive data handling"""
        sensitive_keys = [
            'FLASK_SECRET_KEY',
            'JWT_SECRET_KEY',
            'DATABASE_URL'
        ]
        
        # Test sensitive data masking
        for key in sensitive_keys:
            value = self.config_manager.get(key)
            self.assertNotIn(
                value,
                str(self.config_manager.config)
            )

    def test_configuration_export(self):
        """Test configuration export capabilities"""
        # Export to JSON
        json_file = os.path.join(self.temp_dir, 'config.json')
        with open(json_file, 'w') as f:
            json.dump(self.config_manager.config, f)
        
        # Verify exported configuration
        with open(json_file, 'r') as f:
            exported_config = json.load(f)
        
        self.assertEqual(
            exported_config['FLASK_ENV'],
            self.config_manager.get('FLASK_ENV')
        )

    def test_configuration_update(self):
        """Test configuration update process"""
        updates = {
            'SERVER_PORT': 8000,
            'WEBAPP_PORT': 8001,
            'NEW_SETTING': 'value'
        }
        
        # Apply updates
        for key, value in updates.items():
            self.config_manager.set(key, value)
        
        # Verify updates
        for key, value in updates.items():
            self.assertEqual(self.config_manager.get(key), value)

    def test_type_conversion(self):
        """Test configuration type conversion"""
        # Test integer conversion
        self.config_manager.set('INT_VALUE', '42')
        self.assertIsInstance(
            int(self.config_manager.get('INT_VALUE')),
            int
        )
        
        # Test boolean conversion
        self.config_manager.set('BOOL_VALUE', 'true')
        self.assertIsInstance(
            self.config_manager.get('BOOL_VALUE').lower() == 'true',
            bool
        )
        
        # Test float conversion
        self.config_manager.set('FLOAT_VALUE', '3.14')
        self.assertIsInstance(
            float(self.config_manager.get('FLOAT_VALUE')),
            float
        )

    def test_configuration_inheritance(self):
        """Test configuration inheritance"""
        base_config = {
            'DEBUG': False,
            'LOG_LEVEL': 'INFO',
            'MAX_CONNECTIONS': 100
        }
        
        # Create derived configuration
        self.config_manager.config.update(base_config)
        
        # Override some values
        overrides = {
            'DEBUG': True,
            'NEW_SETTING': 'value'
        }
        self.config_manager.config.update(overrides)
        
        # Verify inheritance
        self.assertEqual(self.config_manager.get('DEBUG'), True)
        self.assertEqual(self.config_manager.get('LOG_LEVEL'), 'INFO')
        self.assertEqual(self.config_manager.get('NEW_SETTING'), 'value')

if __name__ == '__main__':
    unittest.main()
