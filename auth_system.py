"""
Authentication system for Terminusa Online
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import jwt
import bcrypt
import logging
from functools import wraps
from flask import request, jsonify, current_app

from models import db, User, Player
from models.player import PlayerClass

logger = logging.getLogger(__name__)

class AuthSystem:
    def __init__(self, app):
        self.app = app
        self.logger = logger
        
        # JWT configuration
        self.jwt_secret = app.config['JWT_SECRET_KEY']
        self.jwt_algorithm = 'HS256'
        self.jwt_expiry = timedelta(hours=24)
        
        # Rate limiting
        self.login_attempts = {}
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)

    def register(self, username: str, email: str, password: str, 
                player_name: str, player_class: str) -> Dict:
        """Register a new user and create their player profile"""
        try:
            # Validate input
            if not self._validate_registration_input(username, email, password, player_name):
                return {
                    'success': False,
                    'message': 'Invalid registration input'
                }

            # Check if username or email already exists
            if User.query.filter(
                (User.username == username) | (User.email == email)
            ).first():
                return {
                    'success': False,
                    'message': 'Username or email already exists'
                }

            # Hash password
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            )

            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                registered_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()  # Get user.id without committing

            # Create player profile
            try:
                player_class_enum = PlayerClass[player_class.upper()]
            except KeyError:
                return {
                    'success': False,
                    'message': 'Invalid player class'
                }

            player = Player(
                user_id=user.id,
                name=player_name,
                player_class=player_class_enum
            )
            db.session.add(player)

            # Commit both user and player
            db.session.commit()

            # Generate initial token
            token = self._generate_token(user)

            return {
                'success': True,
                'message': 'Registration successful',
                'token': token,
                'user': user.to_dict(),
                'player': player.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Registration error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Registration failed'
            }

    def login(self, username: str, password: str) -> Dict:
        """Login a user"""
        try:
            # Check rate limiting
            if self._is_rate_limited(username):
                return {
                    'success': False,
                    'message': 'Too many login attempts. Try again later.'
                }

            # Get user
            user = User.query.filter_by(username=username).first()
            if not user:
                self._record_failed_attempt(username)
                return {
                    'success': False,
                    'message': 'Invalid username or password'
                }

            # Check password
            if not bcrypt.checkpw(
                password.encode('utf-8'),
                user.password_hash
            ):
                self._record_failed_attempt(username)
                return {
                    'success': False,
                    'message': 'Invalid username or password'
                }

            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Generate token
            token = self._generate_token(user)

            # Clear failed attempts
            self._clear_failed_attempts(username)

            return {
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict()
            }

        except Exception as e:
            self.logger.error(f"Login error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Login failed'
            }

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            # Check if token is expired
            exp = datetime.fromtimestamp(payload['exp'])
            if exp < datetime.utcnow():
                return False, None
                
            return True, payload

        except jwt.InvalidTokenError:
            return False, None

    def refresh_token(self, token: str) -> Dict:
        """Refresh JWT token"""
        try:
            valid, payload = self.verify_token(token)
            if not valid:
                return {
                    'success': False,
                    'message': 'Invalid token'
                }

            # Get user
            user = User.query.get(payload['user_id'])
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }

            # Generate new token
            new_token = self._generate_token(user)

            return {
                'success': True,
                'message': 'Token refreshed',
                'token': new_token
            }

        except Exception as e:
            self.logger.error(f"Token refresh error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Token refresh failed'
            }

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict:
        """Change user password"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }

            # Verify old password
            if not bcrypt.checkpw(
                old_password.encode('utf-8'),
                user.password_hash
            ):
                return {
                    'success': False,
                    'message': 'Invalid password'
                }

            # Validate new password
            if not self._validate_password(new_password):
                return {
                    'success': False,
                    'message': 'Invalid new password'
                }

            # Update password
            user.password_hash = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt()
            )
            db.session.commit()

            return {
                'success': True,
                'message': 'Password changed successfully'
            }

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Password change error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Password change failed'
            }

    def _generate_token(self, user: User) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + self.jwt_expiry
        }
        return jwt.encode(
            payload,
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )

    def _validate_registration_input(self, username: str, email: str, 
                                   password: str, player_name: str) -> bool:
        """Validate registration input"""
        if not all([username, email, password, player_name]):
            return False
            
        if not self._validate_username(username):
            return False
            
        if not self._validate_email(email):
            return False
            
        if not self._validate_password(password):
            return False
            
        if not self._validate_player_name(player_name):
            return False
            
        return True

    def _validate_username(self, username: str) -> bool:
        """Validate username format"""
        # 3-20 characters, alphanumeric and underscore only
        if not username or len(username) < 3 or len(username) > 20:
            return False
        return username.isalnum() or '_' in username

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        # Basic email validation
        if not email or '@' not in email or '.' not in email:
            return False
        return len(email) <= 255

    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        # At least 8 characters, must contain numbers and letters
        if not password or len(password) < 8:
            return False
        return any(c.isalpha() for c in password) and any(c.isdigit() for c in password)

    def _validate_player_name(self, name: str) -> bool:
        """Validate player name format"""
        # 2-20 characters, letters and spaces only
        if not name or len(name) < 2 or len(name) > 20:
            return False
        return all(c.isalpha() or c.isspace() for c in name)

    def _is_rate_limited(self, username: str) -> bool:
        """Check if login attempts are rate limited"""
        if username in self.login_attempts:
            attempts = self.login_attempts[username]
            if len(attempts) >= self.max_attempts:
                oldest_attempt = min(attempts)
                if datetime.utcnow() - oldest_attempt < self.lockout_duration:
                    return True
                else:
                    self._clear_failed_attempts(username)
        return False

    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        if username not in self.login_attempts:
            self.login_attempts[username] = []
        self.login_attempts[username].append(datetime.utcnow())

    def _clear_failed_attempts(self, username: str):
        """Clear failed login attempts"""
        if username in self.login_attempts:
            del self.login_attempts[username]

def login_required(f):
    """Decorator for routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': 'No authentication token provided'
            }), 401

        token = auth_header.split(' ')[1]
        auth_system = current_app.auth_system
        valid, payload = auth_system.verify_token(token)

        if not valid:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401

        # Add user info to request
        request.user_id = payload['user_id']
        request.username = payload['username']
        
        return f(*args, **kwargs)
        
    return decorated_function
