import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum, auto
import json
import uuid

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AuditAction(Enum):
    """Audit action types"""
    USER_LOGIN = auto()
    USER_LOGOUT = auto()
    USER_CREATE = auto()
    USER_DELETE = auto()
    USER_UPDATE = auto()
    USER_BAN = auto()
    USER_UNBAN = auto()
    
    ITEM_CREATE = auto()
    ITEM_DELETE = auto()
    ITEM_MODIFY = auto()
    ITEM_TRADE = auto()
    
    GUILD_CREATE = auto()
    GUILD_DELETE = auto()
    GUILD_MODIFY = auto()
    
    ADMIN_ACTION = auto()
    CONFIG_CHANGE = auto()
    PERMISSION_CHANGE = auto()
    CURRENCY_MINT = auto()
    MAINTENANCE_MODE = auto()

class AuditSeverity(Enum):
    """Audit severity levels"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

@dataclass
class AuditEntry:
    """Audit entry data"""
    id: str
    timestamp: datetime
    action: AuditAction
    severity: AuditSeverity
    user_id: int
    target_id: Optional[int]
    ip_address: str
    details: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class AuditSystem:
    """System for tracking and auditing actions"""
    def __init__(self, storage_dir: str = 'audit_logs'):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.current_file = None
        self.current_date = None
        self._rotate_file()

    def log_action(
        self,
        action: AuditAction,
        user_id: int,
        ip_address: str,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.INFO,
        target_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """Log an audited action"""
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            action=action,
            severity=severity,
            user_id=user_id,
            target_id=target_id,
            ip_address=ip_address,
            details=details,
            metadata=metadata
        )
        
        self._write_entry(entry)
        return entry

    def get_entries(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        actions: Optional[List[AuditAction]] = None,
        user_id: Optional[int] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Get audit entries with filtering"""
        entries = []
        
        # Determine date range
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=7)
        if end_time is None:
            end_time = datetime.utcnow()
        
        # Get relevant files
        current = start_time.date()
        while current <= end_time.date():
            file_path = os.path.join(
                self.storage_dir,
                f"audit_{current.isoformat()}.log"
            )
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    for line in f:
                        entry = self._parse_entry(line)
                        if entry and self._filter_entry(
                            entry,
                            start_time,
                            end_time,
                            actions,
                            user_id,
                            severity
                        ):
                            entries.append(entry)
                            if len(entries) >= limit:
                                return entries[:limit]
            
            current += timedelta(days=1)
        
        return entries

    def get_user_history(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Get audit history for user"""
        return self.get_entries(user_id=user_id, limit=limit)

    def get_critical_events(
        self,
        hours: int = 24
    ) -> List[AuditEntry]:
        """Get critical events within time period"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return self.get_entries(
            start_time=start_time,
            severity=AuditSeverity.CRITICAL
        )

    def _write_entry(self, entry: AuditEntry):
        """Write audit entry to file"""
        self._rotate_file()
        
        data = {
            'id': entry.id,
            'timestamp': entry.timestamp.isoformat(),
            'action': entry.action.name,
            'severity': entry.severity.name,
            'user_id': entry.user_id,
            'target_id': entry.target_id,
            'ip_address': entry.ip_address,
            'details': entry.details,
            'metadata': entry.metadata
        }
        
        with open(self.current_file, 'a') as f:
            f.write(json.dumps(data) + '\n')

    def _rotate_file(self):
        """Rotate audit log file if needed"""
        current_date = datetime.utcnow().date()
        if current_date != self.current_date:
            self.current_date = current_date
            self.current_file = os.path.join(
                self.storage_dir,
                f"audit_{current_date.isoformat()}.log"
            )

    def _parse_entry(self, line: str) -> Optional[AuditEntry]:
        """Parse audit entry from log line"""
        try:
            data = json.loads(line)
            return AuditEntry(
                id=data['id'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                action=AuditAction[data['action']],
                severity=AuditSeverity[data['severity']],
                user_id=data['user_id'],
                target_id=data['target_id'],
                ip_address=data['ip_address'],
                details=data['details'],
                metadata=data['metadata']
            )
        except Exception:
            return None

    def _filter_entry(
        self,
        entry: AuditEntry,
        start_time: datetime,
        end_time: datetime,
        actions: Optional[List[AuditAction]],
        user_id: Optional[int],
        severity: Optional[AuditSeverity]
    ) -> bool:
        """Filter audit entry based on criteria"""
        if entry.timestamp < start_time or entry.timestamp > end_time:
            return False
        
        if actions and entry.action not in actions:
            return False
        
        if user_id is not None and entry.user_id != user_id:
            return False
        
        if severity is not None and entry.severity != severity:
            return False
        
        return True

class TestAudit(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_dir = "test_audit_logs"
        self.audit = AuditSystem(self.test_dir)

    def tearDown(self):
        """Clean up after each test"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_basic_logging(self):
        """Test basic audit logging"""
        # Log action
        entry = self.audit.log_action(
            AuditAction.USER_LOGIN,
            user_id=1,
            ip_address="127.0.0.1",
            details={"browser": "Chrome"}
        )
        
        # Get entries
        entries = self.audit.get_entries()
        
        # Verify logging
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].action, AuditAction.USER_LOGIN)
        self.assertEqual(entries[0].user_id, 1)

    def test_filtering(self):
        """Test audit entry filtering"""
        # Log different actions
        self.audit.log_action(
            AuditAction.USER_LOGIN,
            user_id=1,
            ip_address="127.0.0.1",
            details={}
        )
        self.audit.log_action(
            AuditAction.USER_LOGOUT,
            user_id=2,
            ip_address="127.0.0.1",
            details={}
        )
        
        # Filter by user
        entries = self.audit.get_entries(user_id=1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].user_id, 1)
        
        # Filter by action
        entries = self.audit.get_entries(
            actions=[AuditAction.USER_LOGIN]
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].action, AuditAction.USER_LOGIN)

    def test_severity_levels(self):
        """Test audit severity levels"""
        # Log actions with different severities
        self.audit.log_action(
            AuditAction.USER_LOGIN,
            user_id=1,
            ip_address="127.0.0.1",
            details={},
            severity=AuditSeverity.INFO
        )
        self.audit.log_action(
            AuditAction.USER_BAN,
            user_id=1,
            ip_address="127.0.0.1",
            details={},
            severity=AuditSeverity.CRITICAL
        )
        
        # Get critical events
        entries = self.audit.get_critical_events()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].severity, AuditSeverity.CRITICAL)

    def test_user_history(self):
        """Test user history retrieval"""
        # Log actions for different users
        self.audit.log_action(
            AuditAction.USER_LOGIN,
            user_id=1,
            ip_address="127.0.0.1",
            details={}
        )
        self.audit.log_action(
            AuditAction.USER_LOGIN,
            user_id=2,
            ip_address="127.0.0.1",
            details={}
        )
        
        # Get user history
        history = self.audit.get_user_history(1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].user_id, 1)

    def test_time_filtering(self):
        """Test time-based filtering"""
        now = datetime.utcnow()
        
        with patch('datetime.datetime') as mock_datetime:
            # Yesterday's action
            mock_datetime.utcnow.return_value = now - timedelta(days=1)
            self.audit.log_action(
                AuditAction.USER_LOGIN,
                user_id=1,
                ip_address="127.0.0.1",
                details={}
            )
            
            # Today's action
            mock_datetime.utcnow.return_value = now
            self.audit.log_action(
                AuditAction.USER_LOGIN,
                user_id=1,
                ip_address="127.0.0.1",
                details={}
            )
        
        # Get today's entries
        entries = self.audit.get_entries(
            start_time=now - timedelta(hours=1)
        )
        self.assertEqual(len(entries), 1)

    def test_metadata_handling(self):
        """Test audit metadata handling"""
        metadata = {
            'session_id': 'abc123',
            'request_id': 'xyz789'
        }
        
        # Log action with metadata
        entry = self.audit.log_action(
            AuditAction.USER_LOGIN,
            user_id=1,
            ip_address="127.0.0.1",
            details={},
            metadata=metadata
        )
        
        # Verify metadata
        entries = self.audit.get_entries()
        self.assertEqual(entries[0].metadata, metadata)

    def test_file_rotation(self):
        """Test audit log file rotation"""
        now = datetime.utcnow()
        
        with patch('datetime.datetime') as mock_datetime:
            # Yesterday's action
            mock_datetime.utcnow.return_value = now - timedelta(days=1)
            self.audit.log_action(
                AuditAction.USER_LOGIN,
                user_id=1,
                ip_address="127.0.0.1",
                details={}
            )
            
            # Today's action
            mock_datetime.utcnow.return_value = now
            self.audit.log_action(
                AuditAction.USER_LOGIN,
                user_id=1,
                ip_address="127.0.0.1",
                details={}
            )
        
        # Verify file creation
        files = os.listdir(self.test_dir)
        self.assertEqual(len(files), 2)

    def test_target_tracking(self):
        """Test target user tracking"""
        # Log action with target
        entry = self.audit.log_action(
            AuditAction.USER_BAN,
            user_id=1,  # Admin
            target_id=2,  # Banned user
            ip_address="127.0.0.1",
            details={"reason": "Violation"}
        )
        
        # Verify target tracking
        entries = self.audit.get_entries()
        self.assertEqual(entries[0].target_id, 2)

    def test_admin_actions(self):
        """Test admin action auditing"""
        # Log admin actions
        self.audit.log_action(
            AuditAction.CONFIG_CHANGE,
            user_id=1,
            ip_address="127.0.0.1",
            details={
                "setting": "maintenance_mode",
                "value": True
            },
            severity=AuditSeverity.WARNING
        )
        
        # Get admin actions
        entries = self.audit.get_entries(
            actions=[
                AuditAction.CONFIG_CHANGE,
                AuditAction.ADMIN_ACTION
            ]
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0].action,
            AuditAction.CONFIG_CHANGE
        )

if __name__ == '__main__':
    unittest.main()
