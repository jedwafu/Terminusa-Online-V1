import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User

class FriendStatus(Enum):
    """Friend relationship status"""
    PENDING = auto()
    ACCEPTED = auto()
    BLOCKED = auto()

@dataclass
class FriendRequest:
    """Friend request data"""
    id: int
    sender_id: int
    receiver_id: int
    status: FriendStatus
    created_at: datetime
    accepted_at: Optional[datetime] = None

class FriendSystem:
    """Manages friend relationships"""
    def __init__(self):
        self.friends: Dict[int, Set[int]] = {}  # user_id -> friend_ids
        self.requests: Dict[int, FriendRequest] = {}  # request_id -> request
        self.blocked: Dict[int, Set[int]] = {}  # user_id -> blocked_user_ids
        self.next_request_id = 1

    def send_friend_request(
        self,
        sender_id: int,
        receiver_id: int
    ) -> Optional[FriendRequest]:
        """Send a friend request"""
        # Check if already friends
        if (sender_id in self.friends and 
            receiver_id in self.friends[sender_id]):
            return None
        
        # Check if blocked
        if (receiver_id in self.blocked and 
            sender_id in self.blocked[receiver_id]):
            return None
        
        # Check for existing request
        for request in self.requests.values():
            if (request.sender_id == sender_id and 
                request.receiver_id == receiver_id and
                request.status == FriendStatus.PENDING):
                return None
        
        # Create request
        request = FriendRequest(
            id=self.next_request_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            status=FriendStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self.requests[self.next_request_id] = request
        self.next_request_id += 1
        
        return request

    def accept_friend_request(self, request_id: int) -> bool:
        """Accept a friend request"""
        request = self.requests.get(request_id)
        if not request or request.status != FriendStatus.PENDING:
            return False
        
        # Add to friends lists
        if request.sender_id not in self.friends:
            self.friends[request.sender_id] = set()
        if request.receiver_id not in self.friends:
            self.friends[request.receiver_id] = set()
        
        self.friends[request.sender_id].add(request.receiver_id)
        self.friends[request.receiver_id].add(request.sender_id)
        
        # Update request status
        request.status = FriendStatus.ACCEPTED
        request.accepted_at = datetime.utcnow()
        
        return True

    def decline_friend_request(self, request_id: int) -> bool:
        """Decline a friend request"""
        if request_id not in self.requests:
            return False
        
        del self.requests[request_id]
        return True

    def remove_friend(self, user_id: int, friend_id: int) -> bool:
        """Remove a friend"""
        if (user_id not in self.friends or 
            friend_id not in self.friends[user_id]):
            return False
        
        self.friends[user_id].remove(friend_id)
        self.friends[friend_id].remove(user_id)
        return True

    def block_user(self, user_id: int, blocked_id: int) -> bool:
        """Block a user"""
        if user_id not in self.blocked:
            self.blocked[user_id] = set()
        
        self.blocked[user_id].add(blocked_id)
        
        # Remove from friends if exists
        if user_id in self.friends and blocked_id in self.friends[user_id]:
            self.remove_friend(user_id, blocked_id)
        
        return True

    def unblock_user(self, user_id: int, blocked_id: int) -> bool:
        """Unblock a user"""
        if user_id not in self.blocked or blocked_id not in self.blocked[user_id]:
            return False
        
        self.blocked[user_id].remove(blocked_id)
        return True

    def get_friends(self, user_id: int) -> Set[int]:
        """Get user's friends"""
        return self.friends.get(user_id, set())

    def get_pending_requests(self, user_id: int) -> List[FriendRequest]:
        """Get pending friend requests"""
        return [
            request for request in self.requests.values()
            if request.receiver_id == user_id and 
            request.status == FriendStatus.PENDING
        ]

    def get_blocked_users(self, user_id: int) -> Set[int]:
        """Get users blocked by user"""
        return self.blocked.get(user_id, set())

class TestFriends(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.friend_system = FriendSystem()
        
        # Create test users
        self.user1_id = 1
        self.user2_id = 2
        self.user3_id = 3

    def test_friend_request(self):
        """Test friend request functionality"""
        # Send request
        request = self.friend_system.send_friend_request(
            self.user1_id,
            self.user2_id
        )
        
        # Verify request
        self.assertIsNotNone(request)
        self.assertEqual(request.sender_id, self.user1_id)
        self.assertEqual(request.receiver_id, self.user2_id)
        self.assertEqual(request.status, FriendStatus.PENDING)

    def test_accept_request(self):
        """Test accepting friend request"""
        # Send and accept request
        request = self.friend_system.send_friend_request(
            self.user1_id,
            self.user2_id
        )
        
        success = self.friend_system.accept_friend_request(request.id)
        
        # Verify friendship
        self.assertTrue(success)
        self.assertIn(self.user2_id, self.friend_system.get_friends(self.user1_id))
        self.assertIn(self.user1_id, self.friend_system.get_friends(self.user2_id))

    def test_decline_request(self):
        """Test declining friend request"""
        # Send and decline request
        request = self.friend_system.send_friend_request(
            self.user1_id,
            self.user2_id
        )
        
        success = self.friend_system.decline_friend_request(request.id)
        
        # Verify request removed
        self.assertTrue(success)
        self.assertNotIn(request.id, self.friend_system.requests)

    def test_remove_friend(self):
        """Test friend removal"""
        # Add friend and remove
        request = self.friend_system.send_friend_request(
            self.user1_id,
            self.user2_id
        )
        self.friend_system.accept_friend_request(request.id)
        
        success = self.friend_system.remove_friend(
            self.user1_id,
            self.user2_id
        )
        
        # Verify removal
        self.assertTrue(success)
        self.assertNotIn(self.user2_id, self.friend_system.get_friends(self.user1_id))
        self.assertNotIn(self.user1_id, self.friend_system.get_friends(self.user2_id))

    def test_blocking(self):
        """Test user blocking"""
        # Block user
        success = self.friend_system.block_user(
            self.user1_id,
            self.user2_id
        )
        
        # Verify block
        self.assertTrue(success)
        self.assertIn(self.user2_id, self.friend_system.get_blocked_users(self.user1_id))
        
        # Try to send friend request while blocked
        request = self.friend_system.send_friend_request(
            self.user2_id,
            self.user1_id
        )
        
        self.assertIsNone(request)

    def test_unblocking(self):
        """Test user unblocking"""
        # Block and unblock user
        self.friend_system.block_user(self.user1_id, self.user2_id)
        success = self.friend_system.unblock_user(self.user1_id, self.user2_id)
        
        # Verify unblock
        self.assertTrue(success)
        self.assertNotIn(
            self.user2_id,
            self.friend_system.get_blocked_users(self.user1_id)
        )

    def test_duplicate_requests(self):
        """Test duplicate friend request handling"""
        # Send first request
        request1 = self.friend_system.send_friend_request(
            self.user1_id,
            self.user2_id
        )
        
        # Try to send duplicate request
        request2 = self.friend_system.send_friend_request(
            self.user1_id,
            self.user2_id
        )
        
        self.assertIsNone(request2)

    def test_pending_requests(self):
        """Test pending request retrieval"""
        # Send multiple requests
        self.friend_system.send_friend_request(self.user1_id, self.user2_id)
        self.friend_system.send_friend_request(self.user3_id, self.user2_id)
        
        # Get pending requests
        pending = self.friend_system.get_pending_requests(self.user2_id)
        
        self.assertEqual(len(pending), 2)

    def test_friend_list(self):
        """Test friend list management"""
        # Add multiple friends
        request1 = self.friend_system.send_friend_request(
            self.user1_id,
            self.user2_id
        )
        self.friend_system.accept_friend_request(request1.id)
        
        request2 = self.friend_system.send_friend_request(
            self.user1_id,
            self.user3_id
        )
        self.friend_system.accept_friend_request(request2.id)
        
        # Verify friend list
        friends = self.friend_system.get_friends(self.user1_id)
        self.assertEqual(len(friends), 2)
        self.assertIn(self.user2_id, friends)
        self.assertIn(self.user3_id, friends)

    def test_block_friend(self):
        """Test blocking existing friend"""
        # Add friend then block
        request = self.friend_system.send_friend_request(
            self.user1_id,
            self.user2_id
        )
        self.friend_system.accept_friend_request(request.id)
        
        self.friend_system.block_user(self.user1_id, self.user2_id)
        
        # Verify friendship removed
        self.assertNotIn(self.user2_id, self.friend_system.get_friends(self.user1_id))

if __name__ == '__main__':
    unittest.main()
