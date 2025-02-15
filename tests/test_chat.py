import unittest
from unittest.mock import Mock, patch
import sys
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ChatChannel(Enum):
    """Chat channel types"""
    GLOBAL = auto()
    LOCAL = auto()
    PARTY = auto()
    GUILD = auto()
    TRADE = auto()
    PRIVATE = auto()
    SYSTEM = auto()

@dataclass
class ChatMessage:
    """Chat message data"""
    id: int
    channel: ChatChannel
    sender_id: int
    sender_name: str
    content: str
    timestamp: datetime
    recipient_id: Optional[int] = None
    party_id: Optional[int] = None
    guild_id: Optional[int] = None
    filtered: bool = False

class ChatSystem:
    """Manages game chat functionality"""
    def __init__(self):
        self.channels: Dict[ChatChannel, List[ChatMessage]] = {
            channel: [] for channel in ChatChannel
        }
        self.user_channels: Dict[int, Set[ChatChannel]] = {}
        self.muted_users: Set[int] = set()
        self.next_message_id = 1
        self.max_history = 100
        self.word_filter = set(['banned_word1', 'banned_word2'])

    def send_message(
        self,
        sender_id: int,
        sender_name: str,
        channel: ChatChannel,
        content: str,
        recipient_id: Optional[int] = None,
        party_id: Optional[int] = None,
        guild_id: Optional[int] = None
    ) -> Optional[ChatMessage]:
        """Send a chat message"""
        if sender_id in self.muted_users:
            return None
        
        # Filter content
        filtered_content = self._filter_content(content)
        filtered = filtered_content != content
        
        # Create message
        message = ChatMessage(
            id=self.next_message_id,
            channel=channel,
            sender_id=sender_id,
            sender_name=sender_name,
            content=filtered_content,
            timestamp=datetime.utcnow(),
            recipient_id=recipient_id,
            party_id=party_id,
            guild_id=guild_id,
            filtered=filtered
        )
        self.next_message_id += 1
        
        # Store message
        self.channels[channel].append(message)
        if len(self.channels[channel]) > self.max_history:
            self.channels[channel].pop(0)
        
        return message

    def get_messages(
        self,
        channel: ChatChannel,
        user_id: Optional[int] = None,
        party_id: Optional[int] = None,
        guild_id: Optional[int] = None,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get chat messages"""
        messages = self.channels[channel]
        
        # Filter messages
        if channel == ChatChannel.PRIVATE and user_id:
            messages = [
                m for m in messages
                if m.recipient_id == user_id or m.sender_id == user_id
            ]
        elif channel == ChatChannel.PARTY and party_id:
            messages = [m for m in messages if m.party_id == party_id]
        elif channel == ChatChannel.GUILD and guild_id:
            messages = [m for m in messages if m.guild_id == guild_id]
        
        return messages[-limit:]

    def join_channel(self, user_id: int, channel: ChatChannel):
        """Join a chat channel"""
        if user_id not in self.user_channels:
            self.user_channels[user_id] = set()
        self.user_channels[user_id].add(channel)

    def leave_channel(self, user_id: int, channel: ChatChannel):
        """Leave a chat channel"""
        if user_id in self.user_channels:
            self.user_channels[user_id].discard(channel)

    def mute_user(self, user_id: int):
        """Mute a user"""
        self.muted_users.add(user_id)

    def unmute_user(self, user_id: int):
        """Unmute a user"""
        self.muted_users.discard(user_id)

    def _filter_content(self, content: str) -> str:
        """Filter chat content"""
        words = content.split()
        filtered_words = [
            '*' * len(word) if word.lower() in self.word_filter else word
            for word in words
        ]
        return ' '.join(filtered_words)

class TestChat(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.chat_system = ChatSystem()
        
        # Test users
        self.user1_id = 1
        self.user1_name = "Player1"
        self.user2_id = 2
        self.user2_name = "Player2"
        
        # Join channels
        self.chat_system.join_channel(self.user1_id, ChatChannel.GLOBAL)
        self.chat_system.join_channel(self.user2_id, ChatChannel.GLOBAL)

    def test_basic_messaging(self):
        """Test basic message sending and receiving"""
        # Send message
        message = self.chat_system.send_message(
            self.user1_id,
            self.user1_name,
            ChatChannel.GLOBAL,
            "Hello, world!"
        )
        
        # Get messages
        messages = self.chat_system.get_messages(ChatChannel.GLOBAL)
        
        # Verify message
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "Hello, world!")
        self.assertEqual(messages[0].sender_name, self.user1_name)

    def test_private_messaging(self):
        """Test private messaging"""
        # Send private message
        message = self.chat_system.send_message(
            self.user1_id,
            self.user1_name,
            ChatChannel.PRIVATE,
            "Secret message",
            recipient_id=self.user2_id
        )
        
        # Get messages for recipient
        messages = self.chat_system.get_messages(
            ChatChannel.PRIVATE,
            user_id=self.user2_id
        )
        
        # Verify message
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].recipient_id, self.user2_id)

    def test_channel_management(self):
        """Test channel joining and leaving"""
        # Join trade channel
        self.chat_system.join_channel(self.user1_id, ChatChannel.TRADE)
        
        # Verify channel membership
        channels = self.chat_system.user_channels[self.user1_id]
        self.assertIn(ChatChannel.TRADE, channels)
        
        # Leave channel
        self.chat_system.leave_channel(self.user1_id, ChatChannel.TRADE)
        self.assertNotIn(ChatChannel.TRADE, channels)

    def test_message_filtering(self):
        """Test chat message filtering"""
        # Send message with banned word
        message = self.chat_system.send_message(
            self.user1_id,
            self.user1_name,
            ChatChannel.GLOBAL,
            "Hello banned_word1!"
        )
        
        # Verify filtering
        self.assertTrue(message.filtered)
        self.assertNotIn("banned_word1", message.content)
        self.assertIn("*" * len("banned_word1"), message.content)

    def test_user_muting(self):
        """Test user muting functionality"""
        # Mute user
        self.chat_system.mute_user(self.user1_id)
        
        # Try to send message
        message = self.chat_system.send_message(
            self.user1_id,
            self.user1_name,
            ChatChannel.GLOBAL,
            "This shouldn't work"
        )
        
        # Verify message blocked
        self.assertIsNone(message)
        
        # Unmute and try again
        self.chat_system.unmute_user(self.user1_id)
        message = self.chat_system.send_message(
            self.user1_id,
            self.user1_name,
            ChatChannel.GLOBAL,
            "This should work"
        )
        
        self.assertIsNotNone(message)

    def test_party_chat(self):
        """Test party chat functionality"""
        party_id = 1
        
        # Send party message
        message = self.chat_system.send_message(
            self.user1_id,
            self.user1_name,
            ChatChannel.PARTY,
            "Party message",
            party_id=party_id
        )
        
        # Get party messages
        messages = self.chat_system.get_messages(
            ChatChannel.PARTY,
            party_id=party_id
        )
        
        # Verify message
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].party_id, party_id)

    def test_guild_chat(self):
        """Test guild chat functionality"""
        guild_id = 1
        
        # Send guild message
        message = self.chat_system.send_message(
            self.user1_id,
            self.user1_name,
            ChatChannel.GUILD,
            "Guild message",
            guild_id=guild_id
        )
        
        # Get guild messages
        messages = self.chat_system.get_messages(
            ChatChannel.GUILD,
            guild_id=guild_id
        )
        
        # Verify message
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].guild_id, guild_id)

    def test_message_history(self):
        """Test message history limits"""
        # Send many messages
        for i in range(150):  # More than max_history
            self.chat_system.send_message(
                self.user1_id,
                self.user1_name,
                ChatChannel.GLOBAL,
                f"Message {i}"
            )
        
        # Get messages
        messages = self.chat_system.get_messages(ChatChannel.GLOBAL)
        
        # Verify history limit
        self.assertLessEqual(len(messages), self.chat_system.max_history)
        
        # Verify message order
        self.assertEqual(
            messages[-1].content,
            "Message 149"
        )

    def test_system_messages(self):
        """Test system messages"""
        # Send system message
        message = self.chat_system.send_message(
            0,  # System ID
            "System",
            ChatChannel.SYSTEM,
            "Server maintenance in 5 minutes"
        )
        
        # Get system messages
        messages = self.chat_system.get_messages(ChatChannel.SYSTEM)
        
        # Verify message
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].sender_name, "System")

    def test_trade_channel(self):
        """Test trade channel functionality"""
        # Join trade channel
        self.chat_system.join_channel(self.user1_id, ChatChannel.TRADE)
        
        # Send trade message
        message = self.chat_system.send_message(
            self.user1_id,
            self.user1_name,
            ChatChannel.TRADE,
            "WTS Legendary Sword 1000g"
        )
        
        # Get trade messages
        messages = self.chat_system.get_messages(ChatChannel.TRADE)
        
        # Verify message
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].channel, ChatChannel.TRADE)

if __name__ == '__main__':
    unittest.main()
