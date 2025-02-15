import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum, auto
import uuid

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class GuildRole(Enum):
    """Guild member roles"""
    LEADER = auto()
    OFFICER = auto()
    MEMBER = auto()
    RECRUIT = auto()

class GuildPermission(Enum):
    """Guild permissions"""
    INVITE_MEMBER = auto()
    REMOVE_MEMBER = auto()
    PROMOTE_MEMBER = auto()
    DEMOTE_MEMBER = auto()
    MODIFY_RANKS = auto()
    MODIFY_SETTINGS = auto()
    MANAGE_TREASURY = auto()
    POST_ANNOUNCEMENTS = auto()

@dataclass
class GuildRank:
    """Guild rank data"""
    name: str
    role: GuildRole
    permissions: Set[GuildPermission]
    min_level: int = 1
    contribution_required: int = 0

@dataclass
class GuildMember:
    """Guild member data"""
    user_id: int
    rank: GuildRank
    joined_at: datetime
    contribution: int = 0
    last_active: Optional[datetime] = None
    notes: Optional[str] = None

@dataclass
class Guild:
    """Guild data"""
    id: str
    name: str
    description: str
    leader_id: int
    created_at: datetime
    level: int
    experience: int
    members: Dict[int, GuildMember]
    ranks: Dict[str, GuildRank]
    treasury: Dict[str, int]
    settings: Dict[str, Any]
    max_members: int

class GuildSystem:
    """System for guild management"""
    def __init__(self):
        self.guilds: Dict[str, Guild] = {}
        self.user_guilds: Dict[int, str] = {}
        self.invites: Dict[str, Set[int]] = {}  # guild_id -> invited_user_ids
        self.default_ranks = {
            "Leader": GuildRank(
                name="Leader",
                role=GuildRole.LEADER,
                permissions=set(GuildPermission)
            ),
            "Officer": GuildRank(
                name="Officer",
                role=GuildRole.OFFICER,
                permissions={
                    GuildPermission.INVITE_MEMBER,
                    GuildPermission.REMOVE_MEMBER,
                    GuildPermission.POST_ANNOUNCEMENTS
                }
            ),
            "Member": GuildRank(
                name="Member",
                role=GuildRole.MEMBER,
                permissions=set()
            ),
            "Recruit": GuildRank(
                name="Recruit",
                role=GuildRole.RECRUIT,
                permissions=set()
            )
        }

    def create_guild(
        self,
        name: str,
        description: str,
        leader_id: int,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a new guild"""
        if leader_id in self.user_guilds:
            return None
        
        guild_id = str(uuid.uuid4())
        guild = Guild(
            id=guild_id,
            name=name,
            description=description,
            leader_id=leader_id,
            created_at=datetime.utcnow(),
            level=1,
            experience=0,
            members={
                leader_id: GuildMember(
                    user_id=leader_id,
                    rank=self.default_ranks["Leader"],
                    joined_at=datetime.utcnow()
                )
            },
            ranks=self.default_ranks.copy(),
            treasury={},
            settings=settings or {},
            max_members=50
        )
        
        self.guilds[guild_id] = guild
        self.user_guilds[leader_id] = guild_id
        self.invites[guild_id] = set()
        
        return guild_id

    def invite_member(
        self,
        guild_id: str,
        inviter_id: int,
        invitee_id: int
    ) -> bool:
        """Invite user to guild"""
        guild = self.guilds.get(guild_id)
        if not guild:
            return False
        
        inviter = guild.members.get(inviter_id)
        if not inviter:
            return False
        
        if GuildPermission.INVITE_MEMBER not in inviter.rank.permissions:
            return False
        
        if invitee_id in self.user_guilds:
            return False
        
        if len(guild.members) >= guild.max_members:
            return False
        
        if invitee_id in self.invites[guild_id]:
            return False
        
        self.invites[guild_id].add(invitee_id)
        return True

    def accept_invite(
        self,
        guild_id: str,
        user_id: int
    ) -> bool:
        """Accept guild invite"""
        guild = self.guilds.get(guild_id)
        if not guild:
            return False
        
        if user_id not in self.invites[guild_id]:
            return False
        
        if user_id in self.user_guilds:
            return False
        
        if len(guild.members) >= guild.max_members:
            return False
        
        # Add member
        guild.members[user_id] = GuildMember(
            user_id=user_id,
            rank=guild.ranks["Recruit"],
            joined_at=datetime.utcnow()
        )
        
        self.user_guilds[user_id] = guild_id
        self.invites[guild_id].remove(user_id)
        
        return True

    def leave_guild(self, user_id: int) -> bool:
        """Leave current guild"""
        guild_id = self.user_guilds.get(user_id)
        if not guild_id:
            return False
        
        guild = self.guilds[guild_id]
        
        # Can't leave if leader
        if user_id == guild.leader_id:
            return False
        
        # Remove member
        del guild.members[user_id]
        del self.user_guilds[user_id]
        
        return True

    def promote_member(
        self,
        guild_id: str,
        promoter_id: int,
        member_id: int,
        new_rank: str
    ) -> bool:
        """Promote guild member"""
        guild = self.guilds.get(guild_id)
        if not guild:
            return False
        
        promoter = guild.members.get(promoter_id)
        member = guild.members.get(member_id)
        if not promoter or not member:
            return False
        
        if GuildPermission.PROMOTE_MEMBER not in promoter.rank.permissions:
            return False
        
        if new_rank not in guild.ranks:
            return False
        
        # Can't promote to leader
        if guild.ranks[new_rank].role == GuildRole.LEADER:
            return False
        
        # Can't promote to same or higher rank than self
        if guild.ranks[new_rank].role.value <= promoter.rank.role.value:
            return False
        
        member.rank = guild.ranks[new_rank]
        return True

    def modify_rank(
        self,
        guild_id: str,
        user_id: int,
        rank_name: str,
        permissions: Set[GuildPermission]
    ) -> bool:
        """Modify guild rank permissions"""
        guild = self.guilds.get(guild_id)
        if not guild:
            return False
        
        member = guild.members.get(user_id)
        if not member:
            return False
        
        if GuildPermission.MODIFY_RANKS not in member.rank.permissions:
            return False
        
        if rank_name not in guild.ranks:
            return False
        
        # Can't modify leader rank
        if guild.ranks[rank_name].role == GuildRole.LEADER:
            return False
        
        guild.ranks[rank_name].permissions = permissions
        return True

    def update_contribution(
        self,
        user_id: int,
        amount: int
    ) -> bool:
        """Update member contribution"""
        guild_id = self.user_guilds.get(user_id)
        if not guild_id:
            return False
        
        guild = self.guilds[guild_id]
        member = guild.members[user_id]
        
        member.contribution += amount
        member.last_active = datetime.utcnow()
        
        return True

    def get_guild(self, guild_id: str) -> Optional[Guild]:
        """Get guild by ID"""
        return self.guilds.get(guild_id)

    def get_member_guild(self, user_id: int) -> Optional[Guild]:
        """Get user's current guild"""
        guild_id = self.user_guilds.get(user_id)
        if not guild_id:
            return None
        return self.guilds.get(guild_id)

class TestGuild(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.guild_system = GuildSystem()

    def test_guild_creation(self):
        """Test guild creation"""
        # Create guild
        guild_id = self.guild_system.create_guild(
            "Test Guild",
            "A test guild",
            1
        )
        
        # Verify creation
        self.assertIsNotNone(guild_id)
        guild = self.guild_system.get_guild(guild_id)
        self.assertEqual(guild.name, "Test Guild")
        self.assertEqual(guild.leader_id, 1)
        self.assertEqual(len(guild.members), 1)

    def test_guild_invitation(self):
        """Test guild invitation"""
        # Create guild
        guild_id = self.guild_system.create_guild(
            "Test Guild",
            "A test guild",
            1
        )
        
        # Send invite
        success = self.guild_system.invite_member(guild_id, 1, 2)
        self.assertTrue(success)
        
        # Accept invite
        success = self.guild_system.accept_invite(guild_id, 2)
        self.assertTrue(success)
        
        # Verify member added
        guild = self.guild_system.get_guild(guild_id)
        self.assertIn(2, guild.members)
        self.assertEqual(
            guild.members[2].rank.role,
            GuildRole.RECRUIT
        )

    def test_guild_leaving(self):
        """Test guild leaving"""
        # Create guild with members
        guild_id = self.guild_system.create_guild(
            "Test Guild",
            "A test guild",
            1
        )
        self.guild_system.invite_member(guild_id, 1, 2)
        self.guild_system.accept_invite(guild_id, 2)
        
        # Member leaves
        success = self.guild_system.leave_guild(2)
        self.assertTrue(success)
        
        # Leader tries to leave
        success = self.guild_system.leave_guild(1)
        self.assertFalse(success)

    def test_member_promotion(self):
        """Test member promotion"""
        # Create guild with members
        guild_id = self.guild_system.create_guild(
            "Test Guild",
            "A test guild",
            1
        )
        self.guild_system.invite_member(guild_id, 1, 2)
        self.guild_system.accept_invite(guild_id, 2)
        
        # Promote member
        success = self.guild_system.promote_member(
            guild_id,
            1,
            2,
            "Officer"
        )
        
        # Verify promotion
        self.assertTrue(success)
        guild = self.guild_system.get_guild(guild_id)
        self.assertEqual(
            guild.members[2].rank.role,
            GuildRole.OFFICER
        )

    def test_rank_modification(self):
        """Test rank modification"""
        # Create guild
        guild_id = self.guild_system.create_guild(
            "Test Guild",
            "A test guild",
            1
        )
        
        # Modify rank permissions
        success = self.guild_system.modify_rank(
            guild_id,
            1,
            "Officer",
            {GuildPermission.INVITE_MEMBER}
        )
        
        # Verify modification
        self.assertTrue(success)
        guild = self.guild_system.get_guild(guild_id)
        self.assertEqual(
            guild.ranks["Officer"].permissions,
            {GuildPermission.INVITE_MEMBER}
        )

    def test_contribution_tracking(self):
        """Test contribution tracking"""
        # Create guild with member
        guild_id = self.guild_system.create_guild(
            "Test Guild",
            "A test guild",
            1
        )
        
        # Update contribution
        success = self.guild_system.update_contribution(1, 100)
        
        # Verify contribution
        self.assertTrue(success)
        guild = self.guild_system.get_guild(guild_id)
        self.assertEqual(guild.members[1].contribution, 100)

    def test_permission_enforcement(self):
        """Test permission enforcement"""
        # Create guild with members
        guild_id = self.guild_system.create_guild(
            "Test Guild",
            "A test guild",
            1
        )
        self.guild_system.invite_member(guild_id, 1, 2)
        self.guild_system.accept_invite(guild_id, 2)
        
        # Regular member tries to promote
        success = self.guild_system.promote_member(
            guild_id,
            2,
            1,
            "Officer"
        )
        
        # Verify failure
        self.assertFalse(success)

    def test_multiple_guilds(self):
        """Test multiple guild handling"""
        # Create two guilds
        guild1_id = self.guild_system.create_guild(
            "Guild 1",
            "First guild",
            1
        )
        guild2_id = self.guild_system.create_guild(
            "Guild 2",
            "Second guild",
            2
        )
        
        # Try to invite member to both
        self.guild_system.invite_member(guild1_id, 1, 3)
        success = self.guild_system.invite_member(guild2_id, 2, 3)
        
        # Should allow multiple invites
        self.assertTrue(success)
        
        # Accept first invite
        self.guild_system.accept_invite(guild1_id, 3)
        
        # Try to accept second
        success = self.guild_system.accept_invite(guild2_id, 3)
        self.assertFalse(success)

    def test_member_limit(self):
        """Test guild member limit"""
        # Create guild with small limit
        guild_id = self.guild_system.create_guild(
            "Test Guild",
            "A test guild",
            1
        )
        guild = self.guild_system.get_guild(guild_id)
        guild.max_members = 2
        
        # Add one member
        self.guild_system.invite_member(guild_id, 1, 2)
        self.guild_system.accept_invite(guild_id, 2)
        
        # Try to add another
        success = self.guild_system.invite_member(guild_id, 1, 3)
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
