import os
from .base import *

# Production Settings
DEBUG = False
TEMPLATE_DEBUG = False

# Security Settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Domain Configuration
ALLOWED_HOSTS = [
    'terminusa.online',
    'play.terminusa.online',
    '46.250.228.210'
]

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'terminusa_db'),
        'USER': os.getenv('DB_USER', 'terminusa_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'sslmode': 'require'
        }
    }
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 1000,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Static and Media Files
STATIC_ROOT = '/var/www/terminusa/static/'
MEDIA_ROOT = '/var/www/terminusa/media/'

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'noreply@terminusa.online'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/terminusa/app.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'terminusa': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

# WebSocket Configuration
WEBSOCKET_URL = 'wss://play.terminusa.online/ws/'
WEBSOCKET_PING_INTERVAL = 30
WEBSOCKET_PING_TIMEOUT = 10

# Game Configuration
GAME_SETTINGS = {
    'max_players_per_gate': 50,
    'gate_refresh_interval': 3600,  # 1 hour
    'territory_update_interval': 300,  # 5 minutes
    'achievement_check_interval': 600,  # 10 minutes
    'currency_decimal_places': 8
}

# AI Configuration
AI_SETTINGS = {
    'model_path': '/var/www/terminusa/ai_models/',
    'max_concurrent_predictions': 100,
    'cache_ttl': 3600,  # 1 hour
    'batch_size': 32
}

# Currency System Settings
CURRENCY_SETTINGS = {
    'solana_network': 'mainnet',
    'solana_rpc_url': os.getenv('SOLANA_RPC_URL'),
    'exon_contract_address': os.getenv('EXON_CONTRACT_ADDRESS'),
    'admin_wallet': 'FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw',
    'transaction_timeout': 30,
    'max_retries': 3
}

# Guild War Settings
GUILD_WAR_SETTINGS = {
    'preparation_time': 86400,  # 24 hours
    'war_duration': 259200,  # 72 hours
    'min_participants': 10,
    'territory_capture_time': 300,  # 5 minutes
    'reinforcement_cooldown': 600  # 10 minutes
}

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_DEFAULT_LIMITS = {
    'game_action': '100/m',
    'auth': '5/m',
    'api': '1000/h'
}

# Security Headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "wss:", "https:")

# Feature Flags
FEATURE_FLAGS = {
    'enable_guild_wars': True,
    'enable_territory_control': True,
    'enable_achievements': True,
    'enable_marketplace': True,
    'enable_gacha': True,
    'enable_referrals': True,
    'enable_loyalty_system': True
}

# Monitoring
PROMETHEUS_EXPORT_METRICS = True
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # percent
    'MEMORY_MIN': 100,  # MB
}

# Backup Configuration
BACKUP_SETTINGS = {
    'backup_dir': '/var/www/backups/',
    'retention_days': 30,
    'compress': True
}

# Admin Configuration
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')
ADMINS = [('Admin', 'admin@terminusa.online')]
