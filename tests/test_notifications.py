import unittest
from unittest.mock import Mock, patch
import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum, auto
from dataclasses import dataclass

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class NotificationType(Enum):
    """Types of notifications"""
    ACHIEVEMENT = auto()
    LEVEL_UP = auto()
    ITEM_DROP = auto()
    PARTY_INVITE = auto()
    GUILD_INVITE = auto()
    TRADE_OFFER = auto()
    SYSTEM_MESSAGE = auto()
    MAINTENANCE = auto()
    REWARD = auto()
    FRIEND_REQUEST = auto()

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Notification:
    """Notification data structure"""
    id: int
    type: NotificationType
    user_id: int
    title: str
    message: str
    priority: NotificationPriority
    timestamp: datetime
    data: Optional[Dict] = None
    read: bool = False
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None

class NotificationManager:
    """Manages user notifications"""
    def __init__(self):
        self.notifications: Dict[int, List[Notification]] = {}
        self.next_id = 1

    def send_notification(self, notification: Notification):
        """Send a notification to a user"""
        if notification.user_id not in self.notifications:
            self.notifications[notification.user_id] = []
        
        notification.id = self.next_id
        self.next_id += 1
        
        self.notifications[notification.user_id].append(notification)
        
        # Clean up expired notifications
        self._cleanup_expired()

    def get_notifications(self, user_id: int, unread_only: bool = False) -> List[Notification]:
        """Get notifications for a user"""
        if user_id not in self.notifications:
            return []
        
        notifications = self.notifications[user_id]
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        return sorted(
            notifications,
            key=lambda n: (n.priority.value, n.timestamp),
            reverse=True
        )

    def mark_as_read(self, user_id: int, notification_id: int):
        """Mark a notification as read"""
        if user_id in self.notifications:
            for notification in self.notifications[user_id]:
                if notification.id == notification_id:
                    notification.read = True
                    break

    def clear_notifications(self, user_id: int):
        """Clear all notifications for a user"""
        if user_id in self.notifications:
            self.notifications[user_id] = []

    def _cleanup_expired(self):
        """Clean up expired notifications"""
        now = datetime.utcnow()
        for user_id in self.notifications:
            self.notifications[user_id] = [
                n for n in self.notifications[user_id]
                if not n.expires_at or n.expires_at > now
            ]

class TestNotifications(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.notification_manager = NotificationManager()
        self.test_user_id = 1

    def test_basic_notification(self):
        """Test basic notification functionality"""
        # Create notification
        notification = Notification(
            id=0,  # Will be set by manager
            type=NotificationType.ACHIEVEMENT,
            user_id=self.test_user_id,
            title="Achievement Unlocked",
            message="You've reached level 10!",
            priority=NotificationPriority.MEDIUM,
            timestamp=datetime.utcnow()
        )
        
        # Send notification
        self.notification_manager.send_notification(notification)
        
        # Get notifications
        notifications = self.notification_manager.get_notifications(self.test_user_id)
        
        # Verify notification
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].type, NotificationType.ACHIEVEMENT)
        self.assertFalse(notifications[0].read)

    def test_notification_priority(self):
        """Test notification priority ordering"""
        # Create notifications with different priorities
        notifications = [
            Notification(
                id=0,
                type=NotificationType.SYSTEM_MESSAGE,
                user_id=self.test_user_id,
                title=f"Test {priority.name}",
                message=f"Priority {priority.name}",
                priority=priority,
                timestamp=datetime.utcnow()
            )
            for priority in NotificationPriority
        ]
        
        # Send notifications in reverse order
        for notification in reversed(notifications):
            self.notification_manager.send_notification(notification)
        
        # Get notifications
        received = self.notification_manager.get_notifications(self.test_user_id)
        
        # Verify priority ordering
        priorities = [n.priority.value for n in received]
        self.assertEqual(priorities, sorted(priorities, reverse=True))

    def test_notification_expiry(self):
        """Test notification expiration"""
        # Create notification that expires soon
        notification = Notification(
            id=0,
            type=NotificationType.PARTY_INVITE,
            user_id=self.test_user_id,
            title="Party Invite",
            message="Join our party!",
            priority=NotificationPriority.MEDIUM,
            timestamp=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=1)
        )
        
        self.notification_manager.send_notification(notification)
        
        # Verify notification exists
        self.assertEqual(
            len(self.notification_manager.get_notifications(self.test_user_id)),
            1
        )
        
        # Wait for expiration
        import time
        time.sleep(1.1)
        
        # Trigger cleanup by sending another notification
        self.notification_manager.send_notification(
            Notification(
                id=0,
                type=NotificationType.SYSTEM_MESSAGE,
                user_id=self.test_user_id,
                title="Test",
                message="Test",
                priority=NotificationPriority.LOW,
                timestamp=datetime.utcnow()
            )
        )
        
        # Verify expired notification is removed
        notifications = self.notification_manager.get_notifications(self.test_user_id)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].type, NotificationType.SYSTEM_MESSAGE)

    def test_read_status(self):
        """Test notification read status"""
        # Create notification
        notification = Notification(
            id=0,
            type=NotificationType.LEVEL_UP,
            user_id=self.test_user_id,
            title="Level Up!",
            message="You've reached level 20!",
            priority=NotificationPriority.MEDIUM,
            timestamp=datetime.utcnow()
        )
        
        self.notification_manager.send_notification(notification)
        
        # Get notification ID
        notification_id = self.notification_manager.get_notifications(
            self.test_user_id
        )[0].id
        
        # Mark as read
        self.notification_manager.mark_as_read(
            self.test_user_id,
            notification_id
        )
        
        # Verify read status
        notifications = self.notification_manager.get_notifications(
            self.test_user_id,
            unread_only=True
        )
        self.assertEqual(len(notifications), 0)

    def test_notification_data(self):
        """Test notification with additional data"""
        # Create notification with data
        notification = Notification(
            id=0,
            type=NotificationType.ITEM_DROP,
            user_id=self.test_user_id,
            title="Item Found",
            message="You found a rare item!",
            priority=NotificationPriority.MEDIUM,
            timestamp=datetime.utcnow(),
            data={
                'item_id': 123,
                'item_name': 'Legendary Sword',
                'rarity': 'Legendary'
            }
        )
        
        self.notification_manager.send_notification(notification)
        
        # Get notification
        notifications = self.notification_manager.get_notifications(self.test_user_id)
        
        # Verify data
        self.assertEqual(notifications[0].data['item_id'], 123)
        self.assertEqual(notifications[0].data['rarity'], 'Legendary')

    def test_notification_actions(self):
        """Test notification with action URLs"""
        # Create notification with action
        notification = Notification(
            id=0,
            type=NotificationType.TRADE_OFFER,
            user_id=self.test_user_id,
            title="Trade Offer",
            message="New trade offer received",
            priority=NotificationPriority.HIGH,
            timestamp=datetime.utcnow(),
            action_url="/trade/offer/123"
        )
        
        self.notification_manager.send_notification(notification)
        
        # Get notification
        notifications = self.notification_manager.get_notifications(self.test_user_id)
        
        # Verify action URL
        self.assertEqual(notifications[0].action_url, "/trade/offer/123")

    def test_notification_cleanup(self):
        """Test notification cleanup"""
        # Create notifications
        self.notification_manager.send_notification(
            Notification(
                id=0,
                type=NotificationType.SYSTEM_MESSAGE,
                user_id=self.test_user_id,
                title="Test 1",
                message="Test 1",
                priority=NotificationPriority.LOW,
                timestamp=datetime.utcnow()
            )
        )
        
        self.notification_manager.send_notification(
            Notification(
                id=0,
                type=NotificationType.SYSTEM_MESSAGE,
                user_id=self.test_user_id,
                title="Test 2",
                message="Test 2",
                priority=NotificationPriority.LOW,
                timestamp=datetime.utcnow()
            )
        )
        
        # Clear notifications
        self.notification_manager.clear_notifications(self.test_user_id)
        
        # Verify notifications cleared
        notifications = self.notification_manager.get_notifications(self.test_user_id)
        self.assertEqual(len(notifications), 0)

    def test_multiple_users(self):
        """Test notifications for multiple users"""
        user_ids = [1, 2, 3]
        
        # Send notifications to different users
        for user_id in user_ids:
            self.notification_manager.send_notification(
                Notification(
                    id=0,
                    type=NotificationType.SYSTEM_MESSAGE,
                    user_id=user_id,
                    title=f"Test User {user_id}",
                    message=f"Message for user {user_id}",
                    priority=NotificationPriority.MEDIUM,
                    timestamp=datetime.utcnow()
                )
            )
        
        # Verify each user's notifications
        for user_id in user_ids:
            notifications = self.notification_manager.get_notifications(user_id)
            self.assertEqual(len(notifications), 1)
            self.assertEqual(
                notifications[0].message,
                f"Message for user {user_id}"
            )

if __name__ == '__main__':
    unittest.main()
