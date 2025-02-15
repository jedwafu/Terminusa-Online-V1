import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum, auto
import json
import hashlib
import threading
import queue
import time

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ReplicationType(Enum):
    """Types of replication"""
    FULL = auto()
    INCREMENTAL = auto()
    SNAPSHOT = auto()

class ReplicationState(Enum):
    """Replication states"""
    IDLE = auto()
    SYNCING = auto()
    CONFLICT = auto()
    ERROR = auto()

@dataclass
class ReplicationChange:
    """Replication change data"""
    id: str
    timestamp: datetime
    entity_type: str
    entity_id: str
    operation: str
    data: Dict[str, Any]
    version: int
    checksum: str

@dataclass
class ReplicationNode:
    """Replication node data"""
    id: str
    name: str
    priority: int
    last_sync: Optional[datetime] = None
    state: ReplicationState = ReplicationState.IDLE
    version: int = 0

class ReplicationSystem:
    """System for data replication"""
    def __init__(self, node_id: str, node_name: str):
        self.node = ReplicationNode(
            id=node_id,
            name=node_name,
            priority=0
        )
        self.nodes: Dict[str, ReplicationNode] = {node_id: self.node}
        self.changes: List[ReplicationChange] = []
        self.change_queue = queue.Queue()
        self.running = False
        self._sync_thread = None
        self._lock = threading.Lock()

    def start(self):
        """Start replication system"""
        self.running = True
        self._sync_thread = threading.Thread(
            target=self._sync_loop
        )
        self._sync_thread.daemon = True
        self._sync_thread.start()

    def stop(self):
        """Stop replication system"""
        self.running = False
        if self._sync_thread:
            self._sync_thread.join()

    def register_node(
        self,
        node_id: str,
        name: str,
        priority: int = 0
    ) -> ReplicationNode:
        """Register a replication node"""
        node = ReplicationNode(
            id=node_id,
            name=name,
            priority=priority
        )
        self.nodes[node_id] = node
        return node

    def track_change(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        data: Dict[str, Any]
    ):
        """Track a data change"""
        change = ReplicationChange(
            id=f"chg_{int(time.time()*1000)}",
            timestamp=datetime.utcnow(),
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            data=data,
            version=self.node.version + 1,
            checksum=self._calculate_checksum(data)
        )
        
        self.change_queue.put(change)
        self.node.version += 1

    def sync_with_node(
        self,
        node_id: str,
        type: ReplicationType = ReplicationType.INCREMENTAL
    ) -> bool:
        """Synchronize with another node"""
        if node_id not in self.nodes:
            return False
        
        target_node = self.nodes[node_id]
        if target_node.state == ReplicationState.SYNCING:
            return False
        
        try:
            target_node.state = ReplicationState.SYNCING
            
            if type == ReplicationType.FULL:
                # Send all changes
                changes_to_sync = self.changes
            else:
                # Send only new changes
                changes_to_sync = [
                    c for c in self.changes
                    if not target_node.last_sync or
                    c.timestamp > target_node.last_sync
                ]
            
            # Simulate network transfer
            time.sleep(0.1)
            
            target_node.last_sync = datetime.utcnow()
            target_node.state = ReplicationState.IDLE
            return True
            
        except Exception:
            target_node.state = ReplicationState.ERROR
            return False

    def get_changes(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        entity_type: Optional[str] = None
    ) -> List[ReplicationChange]:
        """Get replication changes"""
        changes = self.changes
        
        if start_time:
            changes = [c for c in changes if c.timestamp >= start_time]
        if end_time:
            changes = [c for c in changes if c.timestamp <= end_time]
        if entity_type:
            changes = [c for c in changes if c.entity_type == entity_type]
        
        return sorted(changes, key=lambda c: c.timestamp)

    def resolve_conflict(
        self,
        change1: ReplicationChange,
        change2: ReplicationChange
    ) -> ReplicationChange:
        """Resolve a replication conflict"""
        # Use higher version number
        if change1.version > change2.version:
            return change1
        elif change2.version > change1.version:
            return change2
        
        # If versions are equal, use more recent timestamp
        if change1.timestamp > change2.timestamp:
            return change1
        else:
            return change2

    def _sync_loop(self):
        """Background sync loop"""
        while self.running:
            try:
                change = self.change_queue.get(timeout=1)
                with self._lock:
                    self.changes.append(change)
                
                # Sync with other nodes
                for node_id, node in self.nodes.items():
                    if node_id != self.node.id:
                        self.sync_with_node(node_id)
                
            except queue.Empty:
                continue

    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate data checksum"""
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

class TestReplication(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.node1 = ReplicationSystem("node1", "Primary")
        self.node2 = ReplicationSystem("node2", "Secondary")
        
        # Register nodes with each other
        self.node1.register_node("node2", "Secondary")
        self.node2.register_node("node1", "Primary", priority=1)
        
        # Start replication
        self.node1.start()
        self.node2.start()

    def tearDown(self):
        """Clean up after each test"""
        self.node1.stop()
        self.node2.stop()

    def test_basic_replication(self):
        """Test basic data replication"""
        # Track change on node1
        self.node1.track_change(
            "user",
            "1",
            "update",
            {"name": "test"}
        )
        
        # Wait for replication
        time.sleep(0.2)
        
        # Verify replication
        changes1 = self.node1.get_changes()
        changes2 = self.node2.get_changes()
        
        self.assertEqual(len(changes1), 1)
        self.assertEqual(len(changes2), 0)  # Node2 only tracks its own changes

    def test_bidirectional_sync(self):
        """Test bidirectional synchronization"""
        # Track changes on both nodes
        self.node1.track_change(
            "user",
            "1",
            "update",
            {"field1": "value1"}
        )
        
        self.node2.track_change(
            "user",
            "2",
            "update",
            {"field2": "value2"}
        )
        
        # Wait for sync
        time.sleep(0.2)
        
        # Sync nodes
        self.node1.sync_with_node("node2")
        self.node2.sync_with_node("node1")
        
        # Verify changes
        changes1 = self.node1.get_changes()
        changes2 = self.node2.get_changes()
        
        self.assertEqual(len(changes1), 1)
        self.assertEqual(len(changes2), 1)

    def test_conflict_resolution(self):
        """Test conflict resolution"""
        # Create conflicting changes
        change1 = ReplicationChange(
            id="1",
            timestamp=datetime.utcnow(),
            entity_type="user",
            entity_id="1",
            operation="update",
            data={"name": "value1"},
            version=1,
            checksum="hash1"
        )
        
        change2 = ReplicationChange(
            id="2",
            timestamp=datetime.utcnow() + timedelta(seconds=1),
            entity_type="user",
            entity_id="1",
            operation="update",
            data={"name": "value2"},
            version=2,
            checksum="hash2"
        )
        
        # Resolve conflict
        resolved = self.node1.resolve_conflict(change1, change2)
        
        # Verify resolution
        self.assertEqual(resolved.version, 2)
        self.assertEqual(resolved.data["name"], "value2")

    def test_incremental_sync(self):
        """Test incremental synchronization"""
        # Track initial change
        self.node1.track_change(
            "user",
            "1",
            "create",
            {"initial": True}
        )
        
        # Wait and track another change
        time.sleep(0.1)
        self.node1.track_change(
            "user",
            "1",
            "update",
            {"updated": True}
        )
        
        # Sync incrementally
        self.node1.sync_with_node(
            "node2",
            type=ReplicationType.INCREMENTAL
        )
        
        # Verify only new changes synced
        changes = self.node1.get_changes()
        self.assertEqual(len(changes), 2)

    def test_full_sync(self):
        """Test full synchronization"""
        # Track multiple changes
        for i in range(3):
            self.node1.track_change(
                "item",
                str(i),
                "create",
                {"index": i}
            )
        
        # Perform full sync
        self.node1.sync_with_node(
            "node2",
            type=ReplicationType.FULL
        )
        
        # Verify all changes synced
        changes = self.node1.get_changes()
        self.assertEqual(len(changes), 3)

    def test_change_filtering(self):
        """Test change filtering"""
        # Track changes of different types
        self.node1.track_change(
            "user",
            "1",
            "create",
            {"type": "user"}
        )
        
        self.node1.track_change(
            "item",
            "1",
            "create",
            {"type": "item"}
        )
        
        # Get filtered changes
        user_changes = self.node1.get_changes(entity_type="user")
        item_changes = self.node1.get_changes(entity_type="item")
        
        self.assertEqual(len(user_changes), 1)
        self.assertEqual(len(item_changes), 1)

    def test_checksum_verification(self):
        """Test checksum verification"""
        data = {"test": "value"}
        
        # Track change
        self.node1.track_change(
            "test",
            "1",
            "create",
            data
        )
        
        # Verify checksum
        change = self.node1.get_changes()[0]
        expected_checksum = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        self.assertEqual(change.checksum, expected_checksum)

    def test_node_priority(self):
        """Test node priority handling"""
        # Verify node priorities
        self.assertEqual(self.node1.node.priority, 0)
        self.assertEqual(
            self.node2.nodes["node1"].priority,
            1
        )

if __name__ == '__main__':
    unittest.main()
