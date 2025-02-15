import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum, auto
import json
import threading
import asyncio

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ResourceType(Enum):
    """Types of resources"""
    CRYSTAL = auto()
    EXON = auto()
    GOLD = auto()
    ENERGY = auto()
    STAMINA = auto()
    EXPERIENCE = auto()
    REPUTATION = auto()
    SKILL_POINT = auto()

class ResourceOperation(Enum):
    """Resource operations"""
    ADD = auto()
    SUBTRACT = auto()
    SET = auto()
    MULTIPLY = auto()
    DIVIDE = auto()

@dataclass
class ResourceLimit:
    """Resource limit configuration"""
    min_value: float
    max_value: float
    regeneration_rate: Optional[float] = None
    regeneration_interval: Optional[int] = None  # seconds

@dataclass
class ResourceTransaction:
    """Resource transaction data"""
    id: str
    timestamp: datetime
    resource_type: ResourceType
    operation: ResourceOperation
    amount: float
    user_id: int
    source: str
    metadata: Optional[Dict[str, Any]] = None

class ResourceSystem:
    """System for resource management"""
    def __init__(self):
        self.resources: Dict[int, Dict[ResourceType, float]] = {}
        self.limits: Dict[ResourceType, ResourceLimit] = {}
        self.transactions: List[ResourceTransaction] = []
        self.regeneration_tasks: Dict[int, asyncio.Task] = {}
        self._lock = threading.Lock()

    def register_resource(
        self,
        resource_type: ResourceType,
        limit: ResourceLimit
    ):
        """Register a resource type"""
        self.limits[resource_type] = limit

    def initialize_user(
        self,
        user_id: int,
        initial_resources: Dict[ResourceType, float]
    ):
        """Initialize user resources"""
        with self._lock:
            if user_id in self.resources:
                return
            
            self.resources[user_id] = {}
            for resource_type, amount in initial_resources.items():
                if resource_type in self.limits:
                    limit = self.limits[resource_type]
                    self.resources[user_id][resource_type] = max(
                        limit.min_value,
                        min(amount, limit.max_value)
                    )
            
            # Start regeneration for applicable resources
            self._start_regeneration(user_id)

    async def modify_resource(
        self,
        user_id: int,
        resource_type: ResourceType,
        operation: ResourceOperation,
        amount: float,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Modify a resource"""
        if user_id not in self.resources:
            return False
        
        if resource_type not in self.limits:
            return False
        
        limit = self.limits[resource_type]
        current = self.resources[user_id].get(resource_type, 0)
        
        # Calculate new value
        if operation == ResourceOperation.ADD:
            new_value = current + amount
        elif operation == ResourceOperation.SUBTRACT:
            new_value = current - amount
        elif operation == ResourceOperation.SET:
            new_value = amount
        elif operation == ResourceOperation.MULTIPLY:
            new_value = current * amount
        else:  # DIVIDE
            if amount == 0:
                return False
            new_value = current / amount
        
        # Apply limits
        new_value = max(limit.min_value, min(new_value, limit.max_value))
        
        # Check if change is significant
        if abs(new_value - current) < 0.0001:
            return False
        
        # Record transaction
        transaction = ResourceTransaction(
            id=f"txn_{len(self.transactions)}",
            timestamp=datetime.utcnow(),
            resource_type=resource_type,
            operation=operation,
            amount=amount,
            user_id=user_id,
            source=source,
            metadata=metadata
        )
        
        with self._lock:
            self.resources[user_id][resource_type] = new_value
            self.transactions.append(transaction)
        
        return True

    def get_resource(
        self,
        user_id: int,
        resource_type: ResourceType
    ) -> Optional[float]:
        """Get resource amount"""
        if user_id not in self.resources:
            return None
        return self.resources[user_id].get(resource_type)

    def get_transactions(
        self,
        user_id: Optional[int] = None,
        resource_type: Optional[ResourceType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[ResourceTransaction]:
        """Get resource transactions"""
        transactions = self.transactions
        
        if user_id is not None:
            transactions = [t for t in transactions if t.user_id == user_id]
        
        if resource_type:
            transactions = [
                t for t in transactions
                if t.resource_type == resource_type
            ]
        
        if start_time:
            transactions = [
                t for t in transactions
                if t.timestamp >= start_time
            ]
        
        if end_time:
            transactions = [
                t for t in transactions
                if t.timestamp <= end_time
            ]
        
        return sorted(transactions, key=lambda t: t.timestamp)

    async def _regenerate_resources(self, user_id: int):
        """Regenerate user resources"""
        while True:
            with self._lock:
                if user_id not in self.resources:
                    break
                
                for resource_type, limit in self.limits.items():
                    if not limit.regeneration_rate:
                        continue
                    
                    current = self.resources[user_id].get(resource_type, 0)
                    if current < limit.max_value:
                        await self.modify_resource(
                            user_id,
                            resource_type,
                            ResourceOperation.ADD,
                            limit.regeneration_rate,
                            "regeneration"
                        )
            
            await asyncio.sleep(
                min(t.regeneration_interval for t in self.limits.values()
                    if t.regeneration_interval)
            )

    def _start_regeneration(self, user_id: int):
        """Start resource regeneration for user"""
        if any(limit.regeneration_rate for limit in self.limits.values()):
            task = asyncio.create_task(
                self._regenerate_resources(user_id)
            )
            self.regeneration_tasks[user_id] = task

class TestResources(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.resources = ResourceSystem()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Register resources
        self.resources.register_resource(
            ResourceType.ENERGY,
            ResourceLimit(
                min_value=0,
                max_value=100,
                regeneration_rate=1,
                regeneration_interval=60
            )
        )
        
        self.resources.register_resource(
            ResourceType.CRYSTAL,
            ResourceLimit(
                min_value=0,
                max_value=float('inf')
            )
        )

    def tearDown(self):
        """Clean up after each test"""
        self.loop.close()

    def test_resource_initialization(self):
        """Test resource initialization"""
        # Initialize user resources
        self.resources.initialize_user(
            1,
            {
                ResourceType.ENERGY: 50,
                ResourceType.CRYSTAL: 1000
            }
        )
        
        # Verify initialization
        self.assertEqual(
            self.resources.get_resource(1, ResourceType.ENERGY),
            50
        )
        self.assertEqual(
            self.resources.get_resource(1, ResourceType.CRYSTAL),
            1000
        )

    def test_resource_modification(self):
        """Test resource modification"""
        # Initialize user
        self.resources.initialize_user(
            1,
            {ResourceType.CRYSTAL: 1000}
        )
        
        # Modify resource
        success = self.loop.run_until_complete(
            self.resources.modify_resource(
                1,
                ResourceType.CRYSTAL,
                ResourceOperation.ADD,
                500,
                "test"
            )
        )
        
        # Verify modification
        self.assertTrue(success)
        self.assertEqual(
            self.resources.get_resource(1, ResourceType.CRYSTAL),
            1500
        )

    def test_resource_limits(self):
        """Test resource limits"""
        # Initialize user
        self.resources.initialize_user(
            1,
            {ResourceType.ENERGY: 100}
        )
        
        # Try to exceed limit
        success = self.loop.run_until_complete(
            self.resources.modify_resource(
                1,
                ResourceType.ENERGY,
                ResourceOperation.ADD,
                50,
                "test"
            )
        )
        
        # Verify limit enforcement
        self.assertFalse(success)
        self.assertEqual(
            self.resources.get_resource(1, ResourceType.ENERGY),
            100
        )

    def test_resource_regeneration(self):
        """Test resource regeneration"""
        # Initialize user with low energy
        self.resources.initialize_user(
            1,
            {ResourceType.ENERGY: 50}
        )
        
        # Wait for regeneration
        self.loop.run_until_complete(asyncio.sleep(1))
        
        # Verify regeneration
        energy = self.resources.get_resource(1, ResourceType.ENERGY)
        self.assertGreater(energy, 50)

    def test_transaction_tracking(self):
        """Test transaction tracking"""
        # Initialize user
        self.resources.initialize_user(
            1,
            {ResourceType.CRYSTAL: 1000}
        )
        
        # Perform transactions
        self.loop.run_until_complete(
            self.resources.modify_resource(
                1,
                ResourceType.CRYSTAL,
                ResourceOperation.ADD,
                500,
                "test"
            )
        )
        
        self.loop.run_until_complete(
            self.resources.modify_resource(
                1,
                ResourceType.CRYSTAL,
                ResourceOperation.SUBTRACT,
                200,
                "test"
            )
        )
        
        # Get transactions
        transactions = self.resources.get_transactions(
            user_id=1,
            resource_type=ResourceType.CRYSTAL
        )
        
        # Verify transactions
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0].amount, 500)
        self.assertEqual(transactions[1].amount, 200)

    def test_resource_operations(self):
        """Test different resource operations"""
        # Initialize user
        self.resources.initialize_user(
            1,
            {ResourceType.CRYSTAL: 1000}
        )
        
        # Test operations
        operations = [
            (ResourceOperation.ADD, 500, 1500),
            (ResourceOperation.SUBTRACT, 200, 1300),
            (ResourceOperation.MULTIPLY, 2, 2600),
            (ResourceOperation.DIVIDE, 2, 1300),
            (ResourceOperation.SET, 2000, 2000)
        ]
        
        for operation, amount, expected in operations:
            success = self.loop.run_until_complete(
                self.resources.modify_resource(
                    1,
                    ResourceType.CRYSTAL,
                    operation,
                    amount,
                    "test"
                )
            )
            
            self.assertTrue(success)
            self.assertEqual(
                self.resources.get_resource(1, ResourceType.CRYSTAL),
                expected
            )

    def test_transaction_filtering(self):
        """Test transaction filtering"""
        # Initialize users
        self.resources.initialize_user(
            1,
            {ResourceType.CRYSTAL: 1000}
        )
        self.resources.initialize_user(
            2,
            {ResourceType.CRYSTAL: 1000}
        )
        
        # Create transactions
        self.loop.run_until_complete(
            self.resources.modify_resource(
                1,
                ResourceType.CRYSTAL,
                ResourceOperation.ADD,
                500,
                "test"
            )
        )
        
        self.loop.run_until_complete(
            self.resources.modify_resource(
                2,
                ResourceType.CRYSTAL,
                ResourceOperation.ADD,
                500,
                "test"
            )
        )
        
        # Filter by user
        transactions = self.resources.get_transactions(user_id=1)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].user_id, 1)

if __name__ == '__main__':
    unittest.main()
