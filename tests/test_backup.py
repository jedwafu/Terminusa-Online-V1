import unittest
from unittest.mock import Mock, patch
import sys
import os
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sqlite3
import hashlib

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class BackupInfo:
    """Backup information"""
    id: str
    timestamp: datetime
    type: str
    size: int
    checksum: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BackupSystem:
    """System for managing backups"""
    def __init__(self, backup_dir: str = 'backups'):
        self.backup_dir = backup_dir
        self.db_path = os.path.join(backup_dir, 'backup_meta.db')
        os.makedirs(backup_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize backup metadata database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                type TEXT,
                size INTEGER,
                checksum TEXT,
                description TEXT,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    def create_backup(
        self,
        source_dir: str,
        backup_type: str = 'full',
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BackupInfo:
        """Create a new backup"""
        # Generate backup ID and path
        timestamp = datetime.utcnow()
        backup_id = f"{backup_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(self.backup_dir, f"{backup_id}.zip")
        
        # Create backup archive
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, source_dir)
                    zf.write(file_path, arc_path)
        
        # Calculate checksum
        checksum = self._calculate_checksum(backup_path)
        
        # Get backup size
        size = os.path.getsize(backup_path)
        
        # Create backup info
        backup_info = BackupInfo(
            id=backup_id,
            timestamp=timestamp,
            type=backup_type,
            size=size,
            checksum=checksum,
            description=description,
            metadata=metadata
        )
        
        # Store metadata
        self._store_backup_info(backup_info)
        
        return backup_info

    def restore_backup(
        self,
        backup_id: str,
        target_dir: str,
        verify: bool = True
    ) -> bool:
        """Restore from backup"""
        backup_path = os.path.join(self.backup_dir, f"{backup_id}.zip")
        
        if not os.path.exists(backup_path):
            return False
        
        # Verify checksum
        if verify:
            backup_info = self.get_backup_info(backup_id)
            if not backup_info:
                return False
            
            current_checksum = self._calculate_checksum(backup_path)
            if current_checksum != backup_info.checksum:
                return False
        
        # Clear target directory
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir)
        
        # Extract backup
        with zipfile.ZipFile(backup_path, 'r') as zf:
            zf.extractall(target_dir)
        
        return True

    def list_backups(
        self,
        backup_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[BackupInfo]:
        """List available backups"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM backups WHERE 1=1"
        params = []
        
        if backup_type:
            query += " AND type = ?"
            params.append(backup_type)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            BackupInfo(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                type=row[2],
                size=row[3],
                checksum=row[4],
                description=row[5],
                metadata=json.loads(row[6]) if row[6] else None
            )
            for row in rows
        ]

    def get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Get backup information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM backups WHERE id = ?",
            (backup_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return BackupInfo(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            type=row[2],
            size=row[3],
            checksum=row[4],
            description=row[5],
            metadata=json.loads(row[6]) if row[6] else None
        )

    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup"""
        backup_path = os.path.join(self.backup_dir, f"{backup_id}.zip")
        
        if not os.path.exists(backup_path):
            return False
        
        # Delete file
        os.remove(backup_path)
        
        # Remove metadata
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
        conn.commit()
        conn.close()
        
        return True

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()

    def _store_backup_info(self, backup: BackupInfo):
        """Store backup metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO backups
            (id, timestamp, type, size, checksum, description, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                backup.id,
                backup.timestamp.isoformat(),
                backup.type,
                backup.size,
                backup.checksum,
                backup.description,
                json.dumps(backup.metadata) if backup.metadata else None
            )
        )
        
        conn.commit()
        conn.close()

class TestBackup(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = tempfile.mkdtemp()
        self.restore_dir = tempfile.mkdtemp()
        
        # Create backup system
        self.backup_system = BackupSystem(self.backup_dir)
        
        # Create test files
        self.test_files = {
            'file1.txt': 'Content 1',
            'file2.txt': 'Content 2',
            'subdir/file3.txt': 'Content 3'
        }
        
        for path, content in self.test_files.items():
            full_path = os.path.join(self.test_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)

    def tearDown(self):
        """Clean up after each test"""
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.backup_dir)
        shutil.rmtree(self.restore_dir)

    def test_backup_creation(self):
        """Test backup creation"""
        # Create backup
        backup_info = self.backup_system.create_backup(
            self.test_dir,
            description="Test backup"
        )
        
        # Verify backup file
        backup_path = os.path.join(
            self.backup_dir,
            f"{backup_info.id}.zip"
        )
        self.assertTrue(os.path.exists(backup_path))
        
        # Verify metadata
        stored_info = self.backup_system.get_backup_info(backup_info.id)
        self.assertEqual(stored_info.description, "Test backup")
        self.assertEqual(stored_info.checksum, backup_info.checksum)

    def test_backup_restore(self):
        """Test backup restoration"""
        # Create and restore backup
        backup_info = self.backup_system.create_backup(self.test_dir)
        success = self.backup_system.restore_backup(
            backup_info.id,
            self.restore_dir
        )
        
        self.assertTrue(success)
        
        # Verify restored files
        for path, content in self.test_files.items():
            restored_path = os.path.join(self.restore_dir, path)
            self.assertTrue(os.path.exists(restored_path))
            with open(restored_path, 'r') as f:
                self.assertEqual(f.read(), content)

    def test_backup_listing(self):
        """Test backup listing"""
        # Create multiple backups
        backups = []
        for i in range(3):
            backup = self.backup_system.create_backup(
                self.test_dir,
                backup_type='test',
                description=f"Backup {i}"
            )
            backups.append(backup)
        
        # List backups
        listed = self.backup_system.list_backups(backup_type='test')
        self.assertEqual(len(listed), 3)
        
        # Verify order (newest first)
        self.assertEqual(listed[0].id, backups[-1].id)

    def test_backup_deletion(self):
        """Test backup deletion"""
        # Create and delete backup
        backup_info = self.backup_system.create_backup(self.test_dir)
        success = self.backup_system.delete_backup(backup_info.id)
        
        self.assertTrue(success)
        
        # Verify deletion
        backup_path = os.path.join(
            self.backup_dir,
            f"{backup_info.id}.zip"
        )
        self.assertFalse(os.path.exists(backup_path))
        
        # Verify metadata removal
        self.assertIsNone(
            self.backup_system.get_backup_info(backup_info.id)
        )

    def test_backup_verification(self):
        """Test backup verification"""
        # Create backup
        backup_info = self.backup_system.create_backup(self.test_dir)
        backup_path = os.path.join(
            self.backup_dir,
            f"{backup_info.id}.zip"
        )
        
        # Modify backup file
        with open(backup_path, 'ab') as f:
            f.write(b'corruption')
        
        # Attempt restore with verification
        success = self.backup_system.restore_backup(
            backup_info.id,
            self.restore_dir,
            verify=True
        )
        
        self.assertFalse(success)

    def test_backup_metadata(self):
        """Test backup metadata"""
        metadata = {
            'version': '1.0',
            'files': 3,
            'total_size': 1024
        }
        
        # Create backup with metadata
        backup_info = self.backup_system.create_backup(
            self.test_dir,
            metadata=metadata
        )
        
        # Verify metadata
        stored_info = self.backup_system.get_backup_info(backup_info.id)
        self.assertEqual(stored_info.metadata, metadata)

    def test_time_filtering(self):
        """Test backup time filtering"""
        now = datetime.utcnow()
        
        with patch('datetime.datetime') as mock_datetime:
            # Yesterday's backup
            mock_datetime.utcnow.return_value = now - timedelta(days=1)
            old_backup = self.backup_system.create_backup(self.test_dir)
            
            # Today's backup
            mock_datetime.utcnow.return_value = now
            new_backup = self.backup_system.create_backup(self.test_dir)
        
        # Get recent backups
        recent = self.backup_system.list_backups(
            start_time=now - timedelta(hours=1)
        )
        
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].id, new_backup.id)

    def test_invalid_backup(self):
        """Test handling of invalid backups"""
        # Test non-existent backup
        success = self.backup_system.restore_backup(
            'nonexistent',
            self.restore_dir
        )
        self.assertFalse(success)
        
        # Test invalid backup deletion
        success = self.backup_system.delete_backup('nonexistent')
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
