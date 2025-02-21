"""
User model for Terminusa Online
"""
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

from models import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.LargeBinary, nullable=False)
    
    # Account Status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.String(255))
    ban_expires = db.Column(db.DateTime)
    
    # Account Security
    last_login = db.Column(db.DateTime)
    last_ip = db.Column(db.String(45))
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    
    # Account Settings
    settings = db.Column(JSONB, nullable=False, default={
        'notifications': {
            'email': True,
            'in_game': True,
            'discord': False
        },
        'privacy': {
            'show_online_status': True,
            'show_achievements': True,
            'allow_friend_requests': True,
            'allow_party_invites': True,
            'allow_guild_invites': True
        },
        'gameplay': {
            'auto_decline_duels': False,
            'hide_combat_numbers': False,
            'show_minimap': True
        }
    })
    
    # Social
    friends = db.Column(JSONB, nullable=False, default=[])
    blocked_users = db.Column(JSONB, nullable=False, default=[])
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=True)
    guild_rank = db.Column(db.String(20), nullable=True)
    
    # Wallet
    solana_balance = db.Column(db.Numeric(precision=18, scale=9), default=0)
    exons_balance = db.Column(db.Numeric(precision=18, scale=9), default=0)
    crystals = db.Column(db.BigInteger, default=0)
    
    # Timestamps
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player = db.relationship('Player', backref='user', uselist=False)
    transactions = db.relationship('Transaction', backref='user')
    achievements = db.relationship('Achievement', backref='user')
    inventory = db.relationship('Inventory', backref='user', uselist=False)

    def __init__(self, username: str, email: str, password_hash: bytes):
        self.username = username
        self.email = email
        self.password_hash = password_hash

    def update_login(self, ip_address: str):
        """Update login information"""
        self.last_login = datetime.utcnow()
        self.last_ip = ip_address
        self.failed_login_attempts = 0
        self.last_failed_login = None

    def record_failed_login(self):
        """Record a failed login attempt"""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()

    def is_locked_out(self) -> bool:
        """Check if account is locked due to failed logins"""
        if self.last_failed_login:
            lockout_duration = datetime.utcnow() - self.last_failed_login
            return (self.failed_login_attempts >= 5 and 
                   lockout_duration.total_seconds() < 900)  # 15 minutes
        return False

    def can_login(self) -> Tuple[bool, str]:
        """Check if user can login"""
        if not self.is_active:
            return False, "Account is inactive"
            
        if self.is_banned:
            if self.ban_expires and self.ban_expires > datetime.utcnow():
                return False, f"Account is banned until {self.ban_expires}"
            elif not self.ban_expires:
                return False, f"Account is permanently banned: {self.ban_reason}"
                
        if self.is_locked_out():
            return False, "Account is temporarily locked"
            
        return True, "OK"

    def update_settings(self, settings: Dict) -> bool:
        """Update user settings"""
        try:
            for category, values in settings.items():
                if category in self.settings:
                    self.settings[category].update(values)
            return True
        except Exception:
            return False

    def add_friend(self, friend_id: int) -> bool:
        """Add a friend"""
        if friend_id not in self.friends:
            self.friends.append(friend_id)
            return True
        return False

    def remove_friend(self, friend_id: int) -> bool:
        """Remove a friend"""
        if friend_id in self.friends:
            self.friends.remove(friend_id)
            return True
        return False

    def block_user(self, user_id: int) -> bool:
        """Block a user"""
        if user_id not in self.blocked_users:
            self.blocked_users.append(user_id)
            # Remove from friends if present
            if user_id in self.friends:
                self.friends.remove(user_id)
            return True
        return False

    def unblock_user(self, user_id: int) -> bool:
        """Unblock a user"""
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            return True
        return False

    def can_manage_guild_settings(self, guild) -> bool:
        """Check if user can manage guild settings"""
        return (self.guild_id == guild.id and 
                self.guild_rank in ['leader', 'officer'])

    def can_promote_members(self, guild) -> bool:
        """Check if user can promote guild members"""
        return (self.guild_id == guild.id and 
                self.guild_rank in ['leader', 'officer'])

    def can_demote_members(self, guild) -> bool:
        """Check if user can demote guild members"""
        return (self.guild_id == guild.id and 
                self.guild_rank in ['leader'])

    def can_kick_members(self, guild) -> bool:
        """Check if user can kick guild members"""
        return (self.guild_id == guild.id and 
                self.guild_rank in ['leader', 'officer'])

    def to_dict(self) -> Dict:
        """Convert user data to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'settings': self.settings,
            'guild': {
                'id': self.guild_id,
                'rank': self.guild_rank
            } if self.guild_id else None,
            'wallet': {
                'solana': str(self.solana_balance),
                'exons': str(self.exons_balance),
                'crystals': self.crystals
            },
            'registered_at': self.registered_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def to_public_dict(self) -> Dict:
        """Convert user data to public dictionary (less sensitive info)"""
        return {
            'id': self.id,
            'username': self.username,
            'guild': {
                'id': self.guild_id,
                'rank': self.guild_rank
            } if self.guild_id else None,
            'settings': {
                'privacy': self.settings['privacy']
            }
        }
