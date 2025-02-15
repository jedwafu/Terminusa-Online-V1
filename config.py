import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev_key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev_jwt_key')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://localhost/terminusa')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Solana
    SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
    ADMIN_WALLET = "FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw"
    ADMIN_USERNAME = "adminbb"
    
    # Game Constants
    GAME_CONSTANTS = {
        # Currency Settings
        'CRYSTAL_MAX_SUPPLY': 100_000_000,
        'INITIAL_INVENTORY_SLOTS': 20,
        'MAX_PARTY_SIZE': 10,
        
        # Tax Rates
        'TAX_RATES': {
            'crystal': 0.13,  # 13% base tax
            'exon': 0.13,    # 13% base tax
            'guild_crystal': 0.02,  # 2% additional guild tax
            'guild_exon': 0.02     # 2% additional guild tax
        },
        
        # Level System
        'LEVEL_SYSTEM': {
            'base_exp_required': 100,  # Base experience required for level 1->2
            'exp_multiplier': 1.5,     # Experience requirement multiplier per level
            'max_level': 999,          # Maximum achievable level
        },
        
        # Combat System
        'COMBAT': {
            'base_hp': 100,
            'base_mp': 100,
            'base_stats': {
                'strength': 10,
                'agility': 10,
                'intelligence': 10,
                'luck': 10
            },
            'stat_growth': {
                'hp_per_level': 10,
                'mp_per_level': 5,
                'stat_per_level': 2
            }
        },
        
        # Gate System
        'GATE_GRADES': {
            'E': {'difficulty': 1.0, 'reward_multiplier': 1.0},
            'D': {'difficulty': 1.2, 'reward_multiplier': 1.3},
            'C': {'difficulty': 1.5, 'reward_multiplier': 1.6},
            'B': {'difficulty': 1.8, 'reward_multiplier': 2.0},
            'A': {'difficulty': 2.2, 'reward_multiplier': 2.5},
            'S': {'difficulty': 2.7, 'reward_multiplier': 3.0},
            'SS': {'difficulty': 3.3, 'reward_multiplier': 4.0},
            'SSS': {'difficulty': 4.0, 'reward_multiplier': 5.0}
        },
        
        # Item Grades
        'ITEM_GRADES': {
            'basic': {'repair_cost': 10, 'durability_loss': 1.0},
            'intermediate': {'repair_cost': 20, 'durability_loss': 0.9},
            'excellent': {'repair_cost': 40, 'durability_loss': 0.8},
            'legendary': {'repair_cost': 80, 'durability_loss': 0.7},
            'immortal': {'repair_cost': 160, 'durability_loss': 0.5}
        },
        
        # Gacha System
        'GACHA': {
            'base_rates': {
                'basic': 0.50,
                'intermediate': 0.30,
                'excellent': 0.15,
                'legendary': 0.04,
                'immortal': 0.01
            },
            'pity_system': {
                'legendary': {'guaranteed_pulls': 100, 'rate_increase': 0.001},
                'immortal': {'guaranteed_pulls': 200, 'rate_increase': 0.0005}
            }
        },
        
        # Guild System
        'GUILD': {
            'creation_cost': {
                'exons': 1000,
                'crystals': 1000
            },
            'max_members': 100,
            'quest_reward_multiplier': 1.2,  # 20% bonus on guild quests
            'min_level_create': 20
        },
        
        # Referral System
        'REFERRAL': {
            'min_referral_level': 50,
            'rewards': {
                100: 1000,  # 1000 crystals for 100 referrals
                500: 6000,  # 6000 crystals for 500 referrals
                1000: 15000  # 15000 crystals for 1000 referrals
            }
        },
        
        # Loyalty System
        'LOYALTY': {
            'monthly_reward_rate': 0.01,  # 1% of holdings
            'bonus_threshold': 0.01,      # Additional bonus for holding >1%
            'bonus_rate': 0.005           # 0.5% additional reward
        },
        
        # Shop System
        'SHOP': {
            'inventory_expansion': {'price': 100, 'slots': 10, 'currency': 'crystal'},
            'rename_license': {'price': 50, 'currency': 'crystal'},
            'job_reset': {'price': 200, 'currency': 'exon'},
            'job_class_license': {'price': 500, 'currency': 'exon'},
            'remote_shop_license': {'price': 300, 'currency': 'exon'},
            'basic_resurrection': {'price': 100, 'currency': 'exon', 'heal_percentage': 50},
            'advanced_resurrection': {'price': 300, 'currency': 'exon', 'heal_percentage': 100}
        }
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SERVER_PORT = int(os.getenv('SERVER_PORT', 5000))
    WEBAPP_PORT = int(os.getenv('WEBAPP_PORT', 5001))

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SERVER_PORT = int(os.getenv('SERVER_PORT', 443))
    WEBAPP_PORT = int(os.getenv('WEBAPP_PORT', 443))
    
    # SSL Configuration
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', '/etc/letsencrypt/live/play.terminusa.online/fullchain.pem')
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH', '/etc/letsencrypt/live/play.terminusa.online/privkey.pem')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SERVER_PORT = 5000
    WEBAPP_PORT = 5001

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Get current configuration
def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
