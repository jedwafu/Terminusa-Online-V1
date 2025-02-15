import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum, auto
import jwt
import uuid
import json
import redis

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SessionStatus(Enum):
    """Session status states"""
    ACTIVE = auto()
    EXPIRED = auto()
    TERMINATED = auto()
    LOCKED = auto()

@dataclass
class SessionData:
    """Session data"""
    id: str
    user_id: int
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    status: SessionStatus
    data: Dict[str, Any]

class SessionError(Exception):
    """Session error"""
    pass

class SessionSystem:
    """Manages user sessions"""
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        self.redis = redis.from_url(redis_url)
        self.jwt_secret = "test-jwt-secret"
        self.session_timeout = timedelta(hours=24)
        self.max_sessions_per_user = 5
        self.max_failed_attempts = 3
        self.lockout_duration = timedelta(minutes=15)

    def create_session(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
        data: Optional[Dict] = None
    ) -> SessionData:
        """Create new session"""
        # Check existing sessions
        existing = self.get_user_sessions(user_id)
        if len(existing) >= self.max_sessions_per_user:
            raise SessionError("Maximum sessions exceeded")
        
        # Create session
        now = datetime.utcnow()
        session = SessionData(
            id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=now,
            expires_at=now + self.session_timeout,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            status=SessionStatus.ACTIVE,
            data=data or {}
        )
        
        # Store session
        self._save_session(session)
        
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        data = self.redis.get(f"session:{session_id}")
        if not data:
            return None
        
        return self._deserialize_session(data)

    def get_user_sessions(self, user_id: int) -> List[SessionData]:
        """Get all sessions for user"""
        pattern = f"session:*"
        sessions = []
        
        for key in self.redis.scan_iter(pattern):
            data = self.redis.get(key)
            session = self._deserialize_session(data)
            if session.user_id == user_id:
                sessions.append(session)
        
        return sessions

    def update_session(
        self,
        session_id: str,
        data: Optional[Dict] = None
    ) -> Optional[SessionData]:
        """Update session data"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        if data:
            session.data.update(data)
        
        session.last_activity = datetime.utcnow()
        self._save_session(session)
        
        return session

    def terminate_session(self, session_id: str) -> bool:
        """Terminate session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.status = SessionStatus.TERMINATED
        self._save_session(session)
        
        return True

    def terminate_user_sessions(self, user_id: int) -> int:
        """Terminate all sessions for user"""
        sessions = self.get_user_sessions(user_id)
        count = 0
        
        for session in sessions:
            if self.terminate_session(session.id):
                count += 1
        
        return count

    def generate_token(self, session: SessionData) -> str:
        """Generate JWT token for session"""
        payload = {
            'session_id': session.id,
            'user_id': session.user_id,
            'exp': int(session.expires_at.timestamp())
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    def validate_token(self, token: str) -> Optional[SessionData]:
        """Validate JWT token and return session"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256']
            )
            
            session = self.get_session(payload['session_id'])
            if not session:
                return None
            
            if session.status != SessionStatus.ACTIVE:
                return None
            
            if datetime.utcnow() >= session.expires_at:
                session.status = SessionStatus.EXPIRED
                self._save_session(session)
                return None
            
            return session
            
        except jwt.InvalidTokenError:
            return None

    def _save_session(self, session: SessionData):
        """Save session to Redis"""
        key = f"session:{session.id}"
        data = {
            'id': session.id,
            'user_id': session.user_id,
            'created_at': session.created_at.isoformat(),
            'expires_at': session.expires_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'ip_address': session.ip_address,
            'user_agent': session.user_agent,
            'status': session.status.name,
            'data': session.data
        }
        
        self.redis.set(key, json.dumps(data))

    def _deserialize_session(self, data: bytes) -> SessionData:
        """Deserialize session from Redis"""
        data = json.loads(data)
        return SessionData(
            id=data['id'],
            user_id=data['user_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            ip_address=data['ip_address'],
            user_agent=data['user_agent'],
            status=SessionStatus[data['status']],
            data=data['data']
        )

class TestSessions(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.session_system = SessionSystem()
        
        # Test user data
        self.user_id = 1
        self.ip_address = "127.0.0.1"
        self.user_agent = "Mozilla/5.0"

    def tearDown(self):
        """Clean up after each test"""
        self.session_system.redis.flushall()

    def test_session_creation(self):
        """Test session creation"""
        # Create session
        session = self.session_system.create_session(
            self.user_id,
            self.ip_address,
            self.user_agent
        )
        
        # Verify session
        self.assertIsNotNone(session)
        self.assertEqual(session.user_id, self.user_id)
        self.assertEqual(session.status, SessionStatus.ACTIVE)
        
        # Verify storage
        stored = self.session_system.get_session(session.id)
        self.assertEqual(stored.id, session.id)

    def test_session_retrieval(self):
        """Test session retrieval"""
        # Create multiple sessions
        sessions = []
        for _ in range(3):
            session = self.session_system.create_session(
                self.user_id,
                self.ip_address,
                self.user_agent
            )
            sessions.append(session)
        
        # Get user sessions
        user_sessions = self.session_system.get_user_sessions(self.user_id)
        self.assertEqual(len(user_sessions), 3)
        
        # Verify session data
        for session in user_sessions:
            self.assertEqual(session.user_id, self.user_id)
            self.assertEqual(session.status, SessionStatus.ACTIVE)

    def test_session_update(self):
        """Test session update"""
        # Create session
        session = self.session_system.create_session(
            self.user_id,
            self.ip_address,
            self.user_agent
        )
        
        # Update session
        new_data = {'key': 'value'}
        updated = self.session_system.update_session(
            session.id,
            new_data
        )
        
        # Verify update
        self.assertEqual(updated.data['key'], 'value')
        self.assertGreater(
            updated.last_activity,
            session.last_activity
        )

    def test_session_termination(self):
        """Test session termination"""
        # Create session
        session = self.session_system.create_session(
            self.user_id,
            self.ip_address,
            self.user_agent
        )
        
        # Terminate session
        success = self.session_system.terminate_session(session.id)
        self.assertTrue(success)
        
        # Verify termination
        terminated = self.session_system.get_session(session.id)
        self.assertEqual(terminated.status, SessionStatus.TERMINATED)

    def test_token_generation(self):
        """Test JWT token generation"""
        # Create session
        session = self.session_system.create_session(
            self.user_id,
            self.ip_address,
            self.user_agent
        )
        
        # Generate token
        token = self.session_system.generate_token(session)
        self.assertIsNotNone(token)
        
        # Validate token
        validated = self.session_system.validate_token(token)
        self.assertEqual(validated.id, session.id)

    def test_session_expiry(self):
        """Test session expiration"""
        # Create session with short timeout
        self.session_system.session_timeout = timedelta(seconds=1)
        session = self.session_system.create_session(
            self.user_id,
            self.ip_address,
            self.user_agent
        )
        
        # Generate token
        token = self.session_system.generate_token(session)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Validate expired token
        validated = self.session_system.validate_token(token)
        self.assertIsNone(validated)
        
        # Check session status
        expired = self.session_system.get_session(session.id)
        self.assertEqual(expired.status, SessionStatus.EXPIRED)

    def test_session_limit(self):
        """Test session limit per user"""
        # Create maximum sessions
        for _ in range(self.session_system.max_sessions_per_user):
            self.session_system.create_session(
                self.user_id,
                self.ip_address,
                self.user_agent
            )
        
        # Try to create another session
        with self.assertRaises(SessionError):
            self.session_system.create_session(
                self.user_id,
                self.ip_address,
                self.user_agent
            )

    def test_bulk_termination(self):
        """Test bulk session termination"""
        # Create multiple sessions
        sessions = []
        for _ in range(3):
            session = self.session_system.create_session(
                self.user_id,
                self.ip_address,
                self.user_agent
            )
            sessions.append(session)
        
        # Terminate all sessions
        count = self.session_system.terminate_user_sessions(self.user_id)
        self.assertEqual(count, 3)
        
        # Verify termination
        active = [
            s for s in self.session_system.get_user_sessions(self.user_id)
            if s.status == SessionStatus.ACTIVE
        ]
        self.assertEqual(len(active), 0)

    def test_invalid_token(self):
        """Test invalid token handling"""
        # Test invalid token
        validated = self.session_system.validate_token("invalid_token")
        self.assertIsNone(validated)
        
        # Test expired token
        session = self.session_system.create_session(
            self.user_id,
            self.ip_address,
            self.user_agent
        )
        session.expires_at = datetime.utcnow() - timedelta(hours=1)
        self.session_system._save_session(session)
        
        token = self.session_system.generate_token(session)
        validated = self.session_system.validate_token(token)
        self.assertIsNone(validated)

    def test_session_data_persistence(self):
        """Test session data persistence"""
        # Create session with data
        initial_data = {'preferences': {'theme': 'dark'}}
        session = self.session_system.create_session(
            self.user_id,
            self.ip_address,
            self.user_agent,
            initial_data
        )
        
        # Update data
        update_data = {'preferences': {'language': 'en'}}
        self.session_system.update_session(session.id, update_data)
        
        # Verify data persistence
        updated = self.session_system.get_session(session.id)
        self.assertEqual(
            updated.data['preferences']['theme'],
            'dark'
        )
        self.assertEqual(
            updated.data['preferences']['language'],
            'en'
        )

if __name__ == '__main__':
    unittest.main()
