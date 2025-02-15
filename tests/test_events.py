import unittest
from unittest.mock import Mock, patch
import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Set
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EventType(Enum):
    """Event types for the game"""
    GATE_ENTER = auto()
    GATE_EXIT = auto()
    COMBAT_START = auto()
    COMBAT_END = auto()
    ITEM_DROP = auto()
    LEVEL_UP = auto()
    PARTY_JOIN = auto()
    PARTY_LEAVE = auto()
    GUILD_JOIN = auto()
    GUILD_LEAVE = auto()
    MARKETPLACE_LIST = auto()
    MARKETPLACE_PURCHASE = auto()
    ACHIEVEMENT_UNLOCK = auto()
    TOKEN_SWAP = auto()
    USER_LOGIN = auto()
    USER_LOGOUT = auto()

@dataclass
class Event:
    """Event data structure"""
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    target: str = None
    metadata: Dict[str, Any] = None

class EventBus:
    """Event bus for pub/sub functionality"""
    def __init__(self):
        self.subscribers: Dict[EventType, Set[Callable]] = {}
        self.history: List[Event] = []
        self.max_history = 1000

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = set()
        self.subscribers[event_type].add(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self.subscribers:
            self.subscribers[event_type].discard(callback)

    def publish(self, event: Event):
        """Publish an event"""
        # Store in history
        self.history.append(event)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # Notify subscribers
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")

    def get_history(self, event_type: EventType = None) -> List[Event]:
        """Get event history"""
        if event_type:
            return [e for e in self.history if e.type == event_type]
        return self.history.copy()

class TestEvents(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.event_bus = EventBus()
        self.received_events = []

    def test_basic_pubsub(self):
        """Test basic publish/subscribe functionality"""
        # Create event handler
        def handle_event(event: Event):
            self.received_events.append(event)
        
        # Subscribe to event
        self.event_bus.subscribe(EventType.GATE_ENTER, handle_event)
        
        # Publish event
        event = Event(
            type=EventType.GATE_ENTER,
            data={'gate_id': 1, 'user_id': 1},
            timestamp=datetime.utcnow(),
            source='test'
        )
        self.event_bus.publish(event)
        
        # Verify event received
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].type, EventType.GATE_ENTER)

    def test_multiple_subscribers(self):
        """Test multiple subscribers for same event"""
        count1 = count2 = 0
        
        def handler1(event: Event):
            nonlocal count1
            count1 += 1
        
        def handler2(event: Event):
            nonlocal count2
            count2 += 1
        
        # Subscribe both handlers
        self.event_bus.subscribe(EventType.COMBAT_START, handler1)
        self.event_bus.subscribe(EventType.COMBAT_START, handler2)
        
        # Publish event
        event = Event(
            type=EventType.COMBAT_START,
            data={'combat_id': 1},
            timestamp=datetime.utcnow(),
            source='test'
        )
        self.event_bus.publish(event)
        
        # Verify both handlers called
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)

    def test_event_history(self):
        """Test event history tracking"""
        # Publish multiple events
        events = [
            Event(
                type=EventType.ITEM_DROP,
                data={'item_id': i},
                timestamp=datetime.utcnow(),
                source='test'
            )
            for i in range(3)
        ]
        
        for event in events:
            self.event_bus.publish(event)
        
        # Get history
        history = self.event_bus.get_history()
        
        # Verify history
        self.assertEqual(len(history), 3)
        self.assertEqual(
            [e.data['item_id'] for e in history],
            [0, 1, 2]
        )

    def test_event_filtering(self):
        """Test event history filtering"""
        # Publish different types of events
        events = [
            Event(
                type=EventType.LEVEL_UP,
                data={'user_id': 1},
                timestamp=datetime.utcnow(),
                source='test'
            ),
            Event(
                type=EventType.ITEM_DROP,
                data={'item_id': 1},
                timestamp=datetime.utcnow(),
                source='test'
            ),
            Event(
                type=EventType.LEVEL_UP,
                data={'user_id': 2},
                timestamp=datetime.utcnow(),
                source='test'
            )
        ]
        
        for event in events:
            self.event_bus.publish(event)
        
        # Filter history
        level_ups = self.event_bus.get_history(EventType.LEVEL_UP)
        
        # Verify filtering
        self.assertEqual(len(level_ups), 2)
        self.assertTrue(all(e.type == EventType.LEVEL_UP for e in level_ups))

    def test_event_unsubscribe(self):
        """Test unsubscribing from events"""
        count = 0
        
        def handler(event: Event):
            nonlocal count
            count += 1
        
        # Subscribe and publish
        self.event_bus.subscribe(EventType.PARTY_JOIN, handler)
        event = Event(
            type=EventType.PARTY_JOIN,
            data={'party_id': 1},
            timestamp=datetime.utcnow(),
            source='test'
        )
        self.event_bus.publish(event)
        self.assertEqual(count, 1)
        
        # Unsubscribe and publish again
        self.event_bus.unsubscribe(EventType.PARTY_JOIN, handler)
        self.event_bus.publish(event)
        self.assertEqual(count, 1)  # Count shouldn't increase

    def test_error_handling(self):
        """Test error handling in event handlers"""
        def failing_handler(event: Event):
            raise ValueError("Handler error")
        
        def working_handler(event: Event):
            self.received_events.append(event)
        
        # Subscribe both handlers
        self.event_bus.subscribe(EventType.GUILD_JOIN, failing_handler)
        self.event_bus.subscribe(EventType.GUILD_JOIN, working_handler)
        
        # Publish event
        event = Event(
            type=EventType.GUILD_JOIN,
            data={'guild_id': 1},
            timestamp=datetime.utcnow(),
            source='test'
        )
        self.event_bus.publish(event)
        
        # Working handler should still receive event
        self.assertEqual(len(self.received_events), 1)

    def test_event_metadata(self):
        """Test event metadata handling"""
        def metadata_handler(event: Event):
            self.received_events.append(event)
        
        # Subscribe handler
        self.event_bus.subscribe(EventType.TOKEN_SWAP, metadata_handler)
        
        # Publish event with metadata
        event = Event(
            type=EventType.TOKEN_SWAP,
            data={'amount': 100},
            timestamp=datetime.utcnow(),
            source='test',
            metadata={
                'gas_fee': 0.01,
                'transaction_hash': '0x123'
            }
        )
        self.event_bus.publish(event)
        
        # Verify metadata
        received = self.received_events[0]
        self.assertEqual(received.metadata['gas_fee'], 0.01)
        self.assertEqual(
            received.metadata['transaction_hash'],
            '0x123'
        )

    def test_event_targeting(self):
        """Test targeted events"""
        def target_handler(event: Event):
            if event.target == 'user_1':
                self.received_events.append(event)
        
        # Subscribe handler
        self.event_bus.subscribe(
            EventType.ACHIEVEMENT_UNLOCK,
            target_handler
        )
        
        # Publish events with different targets
        events = [
            Event(
                type=EventType.ACHIEVEMENT_UNLOCK,
                data={'achievement_id': 1},
                timestamp=datetime.utcnow(),
                source='test',
                target='user_1'
            ),
            Event(
                type=EventType.ACHIEVEMENT_UNLOCK,
                data={'achievement_id': 2},
                timestamp=datetime.utcnow(),
                source='test',
                target='user_2'
            )
        ]
        
        for event in events:
            self.event_bus.publish(event)
        
        # Verify only targeted events received
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(
            self.received_events[0].data['achievement_id'],
            1
        )

    def test_history_limit(self):
        """Test event history size limit"""
        # Publish more events than history limit
        limit = self.event_bus.max_history
        events = [
            Event(
                type=EventType.USER_LOGIN,
                data={'user_id': i},
                timestamp=datetime.utcnow(),
                source='test'
            )
            for i in range(limit + 10)
        ]
        
        for event in events:
            self.event_bus.publish(event)
        
        # Verify history size
        history = self.event_bus.get_history()
        self.assertEqual(len(history), limit)
        
        # Verify oldest events were removed
        user_ids = [e.data['user_id'] for e in history]
        self.assertEqual(min(user_ids), 10)

if __name__ == '__main__':
    unittest.main()
