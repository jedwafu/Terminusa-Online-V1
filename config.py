"""
Configuration for Terminusa Online
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://username:password@localhost:5432/terminusa'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_MAX_OVERFLOW = 5
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Session Configuration
    SESSION_TYPE = 'redis'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # CORS Configuration
    CORS_ORIGINS = [
        'https://terminusa.online',
        'https://play.terminusa.online'
    ]
    if DEBUG:
        CORS_ORIGINS.append('http://localhost:3000')
    
    # Rate Limiting
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STORAGE_URL = os.environ.get(
        'REDIS_URL',
        'redis://localhost:6379/1'
    )
    
    # Security Configuration
    BCRYPT_LOG_ROUNDS = 13
    WTF_CSRF_ENABLED = True
    SECURITY_PASSWORD_SALT = os.environ.get(
        'SECURITY_PASSWORD_SALT',
        'security-salt'
    )
    
    # Mail Configuration
    MAIL_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('SMTP_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('SMTP_USERNAME')
    MAIL_PASSWORD = os.environ.get('SMTP_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get(
        'MAIL_DEFAULT_SENDER',
        'noreply@terminusa.online'
    )
    
    # Game Configuration
    MAX_PARTY_SIZE = 10
    MAX_GUILD_SIZE = 100
    LEVEL_CAP = 999
    INVENTORY_INITIAL_SIZE = 20
    INVENTORY_EXPANSION_SIZE = 10
    INVENTORY_EXPANSION_COST = 100
    
    # Currency Configuration
    CRYSTAL_MAX_SUPPLY = 100_000_000
    EXON_INITIAL_PRICE = 0.1
    CRYSTAL_INITIAL_PRICE = 0.01
    
    # Tax Configuration
    BASE_TAX_RATE = 0.13  # 13%
    GUILD_TAX_RATE = 0.02  # Additional 2%
    
    # AI Configuration
    AI_MODEL_PATH = 'models/ai'
    AI_CONFIDENCE_THRESHOLD = 0.95
    AI_UPDATE_INTERVAL = 3600  # 1 hour
    
    # Logging Configuration
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/terminusa.log'
    LOG_LEVEL = 'INFO'
    
    # Domain Configuration
    MAIN_DOMAIN = os.environ.get('MAIN_DOMAIN', 'terminusa.online')
    PLAY_DOMAIN = os.environ.get('PLAY_DOMAIN', 'play.terminusa.online')
    
    # SSL Configuration
    SSL_CERT_PATH = os.environ.get(
        'SSL_CERT_PATH',
        '/etc/letsencrypt/live/terminusa.online/fullchain.pem'
    )
    SSL_KEY_PATH = os.environ.get(
        'SSL_KEY_PATH',
        '/etc/letsencrypt/live/terminusa.online/privkey.pem'
    )
    
    # Cache Configuration
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get(
        'REDIS_URL',
        'redis://localhost:6379/2'
    )
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Web3 Configuration
    SOLANA_NETWORK = os.environ.get('SOLANA_NETWORK', 'mainnet')
    SOLANA_RPC_URL = os.environ.get(
        'SOLANA_RPC_URL',
        'https://api.mainnet-beta.solana.com'
    )
    EXON_CONTRACT_ADDRESS = os.environ.get('EXON_CONTRACT_ADDRESS')
    
    # Feature Flags
    ENABLE_WEB3 = os.environ.get('ENABLE_WEB3', 'True').lower() == 'true'
    ENABLE_GACHA = os.environ.get('ENABLE_GACHA', 'True').lower() == 'true'
    ENABLE_TRADING = os.environ.get('ENABLE_TRADING', 'True').lower() == 'true'
    ENABLE_GAMBLING = os.environ.get('ENABLE_GAMBLING', 'True').lower() == 'true'
    ENABLE_REFERRALS = os.environ.get('ENABLE_REFERRALS', 'True').lower() == 'true'
    ENABLE_LOYALTY = os.environ.get('ENABLE_LOYALTY', 'True').lower() == 'true'
    ENABLE_GUILD_QUESTS = os.environ.get('ENABLE_GUILD_QUESTS', 'True').lower() == 'true'
    
    # Development Configuration
    if DEBUG:
        # Override settings for development
        SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/terminusa_dev'
        REDIS_URL = 'redis://localhost:6379/0'
        MAIL_SUPPRESS_SEND = True
        WTF_CSRF_ENABLED = False
        BCRYPT_LOG_ROUNDS = 4
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
        RATELIMIT_ENABLED = False

class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    DEBUG = True
    
    # Use separate test database
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/terminusa_test'
    
    # Disable CSRF in testing
    WTF_CSRF_ENABLED = False
    
    # Use faster password hashing
    BCRYPT_LOG_ROUNDS = 4
    
    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False
    
    # Use memory cache in tests
    CACHE_TYPE = 'simple'
    
    # Disable emails in tests
    MAIL_SUPPRESS_SEND = True
    
    # Use shorter token expiration in tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Disable Web3 features in tests
    ENABLE_WEB3 = False
