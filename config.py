import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = os.getenv('FLASK_TESTING', 'False').lower() == 'true'
    ENV = os.getenv('FLASK_ENV', 'production')
    
    # Application Directories
    ROOT_DIR = os.getenv('MAIN_APP_DIR', '/var/www/terminusa-web')
    STATIC_FOLDER = os.getenv('MAIN_STATIC_DIR', os.path.join(ROOT_DIR, 'static'))
    STATIC_URL_PATH = '/static'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    
    # File Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.getenv('MEDIA_DIR', os.path.join(ROOT_DIR, 'media'))
    
    # Email Configuration
    MAIL_SERVER = os.getenv('SMTP_SERVER')
    MAIL_PORT = int(os.getenv('SMTP_PORT', 25))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('SMTP_USER')
    MAIL_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # SSL Configuration
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH')
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH')
    
    # Game Configuration
    INITIAL_CRYSTALS = int(os.getenv('INITIAL_CRYSTALS', 100))
    INITIAL_HUNTER_LEVEL = int(os.getenv('INITIAL_HUNTER_LEVEL', 1))
    MAX_INVENTORY_SLOTS = int(os.getenv('MAX_INVENTORY_SLOTS', 50))
    
    # Development Options
    DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'False').lower() == 'true'
    DEBUG_TOOLBAR = os.getenv('DEBUG_TOOLBAR', 'False').lower() == 'true'
