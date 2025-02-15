import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum, auto
import asyncio
import uuid

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PartyRole(Enum):
    """Party member roles"""
    LEADER = auto()
    MEMBER = auto()

class PartyState(Enum):
    """Party states"""
    FORMING = auto()
    ACTIVE = auto()
    DISBANDED = auto()

@dataclass
class PartyMember:
    """Party member data"""
    user_id: int
    role: PartyRole
    joined_at: datetime
    ready: bool = False
    contribution: Dict[str, float] = None

@dataclass
class Party:
    """Party data"""
    id: str
    name: str
    leader_id: int
    state: PartyState
    members: Dict[int, PartyMember]
    max_size: int
    min_level: int
    max_level: Optional[int]
    created_at: datetime
    activity: Optional[str] = None
    settings: Dict[str, Any] = None

class PartySystem:
    """System for party management"""
    def __init__(self):
        self.parties: Dict[str, Party] = {}
        self.user_parties: Dict[int, str] = {}
        self.invites: Dict[str, Set[int]] = {}  # party_id -> invited_user_ids
        self.default_max_size = 4

    def create_party(
        self,
        leader_id: int,
        name: str,
        max_size: Optional[int] = None,
        min_level: int = 1,
        max_level: Optional[int] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a new party"""
        if leader_id in self.user_parties:
            return None
        
        party_id = str(uuid.uuid4())
        party = Party(
            id=party_id,
            name=name,
            leader_id=leader_id,
            state=PartyState.FORMING,
            members={
                leader_id: PartyMember(
                    user_id=leader_id,
                    role=PartyRole.LEADER,
                    joined_at=datetime.utcnow(),
                    ready=True
                )
            },
            max_size=max_size or self.default_max_size,
            min_level=min_level,
            max_level=max_level,
            created_at=datetime.utcnow(),
            settings=settings or {}
        )
        
        self.parties[party_id] = party
        self.user_parties[leader_id] = party_id
        self.invites[party_id] = set()
        
        return party_id

    def invite_member(
        self,
        party_id: str,
        inviter_id: int,
        invitee_id: int
    ) -> bool:
        """Invite user to party"""
        party = self.parties.get(party_id)
        if not party:
            return False
        
        if inviter_id not in party.members:
            return False
        
        if invitee_id in self.user_parties:
            return False
        
        if len(party.members) >= party.max_size:
            return False
        
        if invitee_id in self.invites[party_id]:
            return False
        
        self.invites[party_id].add(invitee_id)
        return True

    def accept_invite(
        self,
        party_id: str,
        user_id: int
    ) -> bool:
        """Accept party invite"""
        party = self.parties.get(party_id)
        if not party:
            return False
        
        if user_id not in self.invites[party_id]:
            return False
        
        if user_id in self.user_parties:
            return False
        
        if len(party.members) >= party.max_size:
            return False
        
        # Add member
        party.members[user_id] = PartyMember(
            user_id=user_id,
            role=PartyRole.MEMBER,
            joined_at=datetime.utcnow()
        )
        
        self.user_parties[user_id] = party_id
        self.invites[party_id].remove(user_id)
        
        return True

    def leave_party(self, user_id: int) -> bool:
        """Leave current party"""
        party_id = self.user_parties.get(user_id)
        if not party_id:
            return False
        
        party = self.parties[party_id]
        
        # Handle leader leaving
        if user_id == party.leader_id:
            # Try to promote another member
            other_members = [
                mid for mid in party.members.keys()
                if mid != user_id
            ]
            
            if other_members:
                new_leader_id = other_members[0]
                party.leader_id = new_leader_id
                party.members[new_leader_id].role = PartyRole.LEADER
            else:
                # Disband party if no other members
                party.state = PartyState.DISBANDED
                del self.parties[party_id]
                del self.invites[party_id]
        
        # Remove member
        del party.members[user_id]
        del self.user_parties[user_id]
        
        return True

    def set_ready(
        self,
        user_id: int,
        ready: bool = True
    ) -> bool:
        """Set ready status"""
        party_id = self.user_parties.get(user_id)
        if not party_id:
            return False
        
        party = self.parties[party_id]
        if user_id not in party.members:
            return False
        
        party.members[user_id].ready = ready
        
        # Check if all members ready
        if all(m.ready for m in party.members.values()):
            party.state = PartyState.ACTIVE
        else:
            party.state = PartyState.FORMING
        
        return True

    def update_contribution(
        self,
        user_id: int,
        contribution: Dict[str, float]
    ) -> bool:
        """Update member contribution"""
        party_id = self.user_parties.get(user_id)
        if not party_id:
            return False
        
        party = self.parties[party_id]
        if user_id not in party.members:
            return False
        
        party.members[user_id].contribution = contribution
        return True

    def get_party(self, party_id: str) -> Optional[Party]:
        """Get party by ID"""
        return self.parties.get(party_id)

    def get_member_party(self, user_id: int) -> Optional[Party]:
        """Get user's current party"""
        party_id = self.user_parties.get(user_id)
        if not party_id:
            return None
        return self.parties.get(party_id)

class TestParty(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.party_system = PartySystem()

    def test_party_creation(self):
        """Test party creation"""
        # Create party
        party_id = self.party_system.create_party(
            1,
            "Test Party"
        )
        
        # Verify creation
        self.assertIsNotNone(party_id)
        party = self.party_system.get_party(party_id)
        self.assertEqual(party.name, "Test Party")
        self.assertEqual(party.leader_id, 1)
        self.assertEqual(party.state, PartyState.FORMING)

    def test_party_invitation(self):
        """Test party invitation"""
        # Create party
        party_id = self.party_system.create_party(1, "Test Party")
        
        # Send invite
        success = self.party_system.invite_member(party_id, 1, 2)
        self.assertTrue(success)
        
        # Accept invite
        success = self.party_system.accept_invite(party_id, 2)
        self.assertTrue(success)
        
        # Verify member added
        party = self.party_system.get_party(party_id)
        self.assertIn(2, party.members)
        self.assertEqual(party.members[2].role, PartyRole.MEMBER)

    def test_party_leaving(self):
        """Test party leaving"""
        # Create party with members
        party_id = self.party_system.create_party(1, "Test Party")
        self.party_system.invite_member(party_id, 1, 2)
        self.party_system.accept_invite(party_id, 2)
        
        # Member leaves
        success = self.party_system.leave_party(2)
        self.assertTrue(success)
        
        # Verify member removed
        party = self.party_system.get_party(party_id)
        self.assertNotIn(2, party.members)

    def test_leader_leaving(self):
        """Test leader leaving"""
        # Create party with members
        party_id = self.party_system.create_party(1, "Test Party")
        self.party_system.invite_member(party_id, 1, 2)
        self.party_system.accept_invite(party_id, 2)
        
        # Leader leaves
        self.party_system.leave_party(1)
        
        # Verify new leader
        party = self.party_system.get_party(party_id)
        self.assertEqual(party.leader_id, 2)
        self.assertEqual(
            party.members[2].role,
            PartyRole.LEADER
        )

    def test_ready_status(self):
        """Test ready status"""
        # Create party with members
        party_id = self.party_system.create_party(1, "Test Party")
        self.party_system.invite_member(party_id, 1, 2)
        self.party_system.accept_invite(party_id, 2)
        
        # Set ready
        self.party_system.set_ready(1)
        self.party_system.set_ready(2)
        
        # Verify party active
        party = self.party_system.get_party(party_id)
        self.assertEqual(party.state, PartyState.ACTIVE)

    def test_contribution_tracking(self):
        """Test contribution tracking"""
        # Create party
        party_id = self.party_system.create_party(1, "Test Party")
        
        # Update contribution
        success = self.party_system.update_contribution(
            1,
            {'damage': 1000, 'healing': 500}
        )
        
        # Verify contribution
        party = self.party_system.get_party(party_id)
        self.assertEqual(
            party.members[1].contribution['damage'],
            1000
        )

    def test_party_size_limit(self):
        """Test party size limit"""
        # Create party with size limit
        party_id = self.party_system.create_party(
            1,
            "Test Party",
            max_size=2
        )
        
        # Add one member
        self.party_system.invite_member(party_id, 1, 2)
        self.party_system.accept_invite(party_id, 2)
        
        # Try to add another
        success = self.party_system.invite_member(party_id, 1, 3)
        self.assertFalse(success)

    def test_multiple_parties(self):
        """Test multiple party handling"""
        # Create two parties
        party1_id = self.party_system.create_party(1, "Party 1")
        party2_id = self.party_system.create_party(2, "Party 2")
        
        # Try to invite member to both
        self.party_system.invite_member(party1_id, 1, 3)
        success = self.party_system.invite_member(party2_id, 2, 3)
        
        # Should allow multiple invites
        self.assertTrue(success)
        
        # Accept first invite
        self.party_system.accept_invite(party1_id, 3)
        
        # Try to accept second
        success = self.party_system.accept_invite(party2_id, 3)
        self.assertFalse(success)

    def test_party_disbanding(self):
        """Test party disbanding"""
        # Create party with one member
        party_id = self.party_system.create_party(1, "Test Party")
        self.party_system.invite_member(party_id, 1, 2)
        self.party_system.accept_invite(party_id, 2)
        
        # All members leave
        self.party_system.leave_party(2)
        self.party_system.leave_party(1)
        
        # Verify party disbanded
        party = self.party_system.get_party(party_id)
        self.assertIsNone(party)

if __name__ == '__main__':
    unittest.main()
