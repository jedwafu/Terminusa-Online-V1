"""
Security configuration for Terminusa Online Monitoring System.
This file defines security settings, policies, and access controls.
"""

import os
from typing import Dict, List

# Authentication Configuration
AUTH_CONFIG = {
    'token': {
        'secret_key': os.getenv('JWT_SECRET_KEY'),
        'algorithm': 'HS256',
        'expiry': 3600,  # 1 hour
        'refresh_window': 300,  # 5 minutes
        'required_claims': ['sub', 'exp', 'iat', 'role'],
        'issuer': 'terminusa.online'
    },
    'api_key': {
        'header_name': 'X-API-Key',
        'prefix': 'Bearer',
        'length': 32,
        'rotation_period': 90  # days
    },
    'rate_limiting': {
        'enabled': True,
        'window': 3600,  # 1 hour
        'max_requests': {
            'default': 1000,
            'admin': 5000
        },
        'per_ip': True
    }
}

# Authorization Configuration
AUTHORIZATION_CONFIG = {
    'roles': {
        'admin': {
            'name': 'Administrator',
            'permissions': ['*'],
            'description': 'Full system access'
        },
        'operator': {
            'name': 'Operator',
            'permissions': [
                'metrics:read',
                'metrics:write',
                'alerts:read',
                'alerts:write',
                'config:read'
            ],
            'description': 'System operation access'
        },
        'viewer': {
            'name': 'Viewer',
            'permissions': [
                'metrics:read',
                'alerts:read'
            ],
            'description': 'Read-only access'
        }
    },
    'permissions': {
        'metrics:read': 'Read metric data',
        'metrics:write': 'Write metric data',
        'alerts:read': 'Read alert data',
        'alerts:write': 'Write alert data',
        'config:read': 'Read configuration',
        'config:write': 'Write configuration'
    }
}

# Access Control Configuration
ACCESS_CONTROL = {
    'ip_whitelist': [
        '127.0.0.1',
        '46.250.228.210'
    ],
    'allowed_origins': [
        'https://terminusa.online',
        'https://play.terminusa.online'
    ],
    'allowed_methods': ['GET', 'POST'],
    'allowed_headers': [
        'Content-Type',
        'Authorization',
        'X-API-Key'
    ],
    'max_age': 3600
}

# Encryption Configuration
ENCRYPTION_CONFIG = {
    'algorithm': 'AES-256-GCM',
    'key_derivation': 'PBKDF2',
    'iterations': 100000,
    'salt_length': 32,
    'key_length': 32,
    'sensitive_fields': [
        'password',
        'api_key',
        'token',
        'secret'
    ]
}

# SSL/TLS Configuration
SSL_CONFIG = {
    'enabled': True,
    'cert_path': '/etc/ssl/certs/terminusa.crt',
    'key_path': '/etc/ssl/private/terminusa.key',
    'protocols': ['TLSv1.2', 'TLSv1.3'],
    'ciphers': 'HIGH:!aNULL:!MD5',
    'hsts': {
        'enabled': True,
        'max_age': 31536000,  # 1 year
        'include_subdomains': True,
        'preload': True
    }
}

# Security Headers
SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'X-Content-Type-Options': 'nosniff',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Feature-Policy': "camera 'none'; microphone 'none'; geolocation 'none'",
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
}

# Session Security
SESSION_SECURITY = {
    'cookie': {
        'secure': True,
        'httponly': True,
        'samesite': 'Strict',
        'max_age': 3600,  # 1 hour
        'path': '/',
        'domain': '.terminusa.online'
    },
    'csrf': {
        'enabled': True,
        'token_length': 32,
        'cookie_name': 'csrf_token',
        'header_name': 'X-CSRF-Token'
    }
}

# Audit Logging
AUDIT_CONFIG = {
    'enabled': True,
    'events': {
        'authentication': True,
        'authorization': True,
        'configuration': True,
        'data_access': True
    },
    'log_format': {
        'timestamp': '%Y-%m-%d %H:%M:%S',
        'fields': [
            'timestamp',
            'event_type',
            'user',
            'ip_address',
            'action',
            'status',
            'details'
        ]
    },
    'retention': {
        'duration': 365,  # days
        'max_size': '1GB'
    }
}

# Input Validation
INPUT_VALIDATION = {
    'sanitization': {
        'enabled': True,
        'html_escape': True,
        'sql_escape': True
    },
    'validation': {
        'enabled': True,
        'max_length': 1048576,  # 1MB
        'allowed_content_types': [
            'application/json',
            'application/x-www-form-urlencoded'
        ]
    }
}

# Security Monitoring
SECURITY_MONITORING = {
    'enabled': True,
    'checks': {
        'failed_logins': {
            'threshold': 5,
            'window': 300,  # 5 minutes
            'action': 'lockout'
        },
        'suspicious_ips': {
            'threshold': 10,
            'window': 3600,  # 1 hour
            'action': 'block'
        },
        'brute_force': {
            'threshold': 100,
            'window': 3600,  # 1 hour
            'action': 'alert'
        }
    },
    'notifications': {
        'email': True,
        'slack': True
    }
}

# Backup Security
BACKUP_SECURITY = {
    'encryption': {
        'enabled': True,
        'algorithm': 'AES-256-GCM',
        'key_rotation': 90  # days
    },
    'access_control': {
        'restricted': True,
        'allowed_roles': ['admin']
    },
    'retention': {
        'duration': 90,  # days
        'secure_deletion': True
    }
}

def get_auth_config() -> Dict:
    """Get authentication configuration."""
    return AUTH_CONFIG

def get_role_permissions(role: str) -> List[str]:
    """Get permissions for a specific role."""
    return AUTHORIZATION_CONFIG['roles'].get(role, {}).get('permissions', [])

def get_allowed_origins() -> List[str]:
    """Get allowed CORS origins."""
    return ACCESS_CONTROL['allowed_origins']

def get_security_headers() -> Dict:
    """Get security headers configuration."""
    return SECURITY_HEADERS

def get_audit_config() -> Dict:
    """Get audit logging configuration."""
    return AUDIT_CONFIG

def get_security_checks() -> Dict:
    """Get security monitoring checks."""
    return SECURITY_MONITORING['checks']

def is_ip_whitelisted(ip: str) -> bool:
    """Check if an IP is whitelisted."""
    return ip in ACCESS_CONTROL['ip_whitelist']

def get_encryption_config() -> Dict:
    """Get encryption configuration."""
    return ENCRYPTION_CONFIG

def get_ssl_config() -> Dict:
    """Get SSL/TLS configuration."""
    return SSL_CONFIG

def get_session_config() -> Dict:
    """Get session security configuration."""
    return SESSION_SECURITY

def get_backup_security() -> Dict:
    """Get backup security configuration."""
    return BACKUP_SECURITY
