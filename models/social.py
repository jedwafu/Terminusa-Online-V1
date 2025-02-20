from database import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, JSON
import enum

class GuildRank(enum.Enum):
    MASTER = "Master"
    VICE_MASTER = "Vice Master"
    ELDER = "Elder"
    VETERAN = "Veteran"
    MEMBER = "Member"
    RECRUIT = "Recruit"

class PartyRole(enum.Enum):
    LEADER = "Leader"
    MEMBER = "Member"

class FriendStatus(enum.Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    BLOCKED = "Blocked"

class Guild(db.Model):
    __tablename__ = 'guilds'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    creation_cost_exons = Column(Float, nullable=False)
    creation_cost_crystals = Column(Float, nullable=False)
    max_members = Column(Integer, default=100)
    announcement = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship('GuildMember', back_populates='guild')
    quests = relationship('Quest', back_populates='guild')

    def __repr__(self):
        return f'<Guild {self.name} (Level {self.level})>'

    def calculate_tax(self, amount):
        """Calculate guild tax (2%) for transactions"""
        return amount * 0.02

    def can_accept_members(self):
        """Check if guild can accept more members"""
        return len(self.members) < self.max_members

    def get_online_members(self):
        """Get list of online guild members"""
        return [member for member in self.members if member.user.is_online]

class GuildMember(db.Model):
    __tablename__ = 'guild_members'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rank = Column(Enum(GuildRank), default=GuildRank.RECRUIT)
    contribution = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Relationships
    guild = relationship('Guild', back_populates='members')
    user = relationship('User', back_populates='guild_membership')

    def __repr__(self):
        return f'<GuildMember {self.user.username} ({self.rank.value})>'

    def can_manage_members(self):
        """Check if member can manage other members"""
        return self.rank in [GuildRank.MASTER, GuildRank.VICE_MASTER]

    def can_manage_quests(self):
        """Check if member can manage guild quests"""
        return self.rank in [GuildRank.MASTER, GuildRank.VICE_MASTER, GuildRank.ELDER]

class Party(db.Model):
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    leader_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    disbanded_at = Column(DateTime)

    # Party settings
    level_range = Column(Integer, default=10)  # Max level difference between members
    auto_loot_distribution = Column(Boolean, default=True)
    loot_quality_threshold = Column(String(20), default='BASIC')  # Minimum quality for auto-looting

    # Relationships
    leader = relationship('User', foreign_keys=[leader_id])
    members = relationship('PartyMember', back_populates='party')
    gate_sessions = relationship('GateSession', back_populates='party')

    def __repr__(self):
        return f'<Party {self.name} (Leader: {self.leader.username})>'

    def calculate_rewards_share(self, total_reward):
        """Calculate reward share based on number of members"""
        member_count = len(self.members)
        if member_count <= 1:
            return total_reward
        
        # Diminishing returns based on party size
        share_multiplier = 1.0
        for i in range(1, member_count):
            share_multiplier *= 0.9  # 10% reduction per additional member
        
        return total_reward * share_multiplier / member_count

    def get_average_luck(self):
        """Calculate average luck stat of party members"""
        if not self.members:
            return 0
        return sum(member.user.character.luck for member in self.members) / len(self.members)

class PartyMember(db.Model):
    __tablename__ = 'party_members'

    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(Enum(PartyRole), default=PartyRole.MEMBER)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime)

    # Combat stats for current session
    damage_dealt = Column(Float, default=0)
    healing_done = Column(Float, default=0)
    deaths = Column(Integer, default=0)

    # Relationships
    party = relationship('Party', back_populates='members')
    user = relationship('User', back_populates='party_memberships')

    def __repr__(self):
        return f'<PartyMember {self.user.username} ({self.role.value})>'

class Friend(db.Model):
    __tablename__ = 'friends'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    friend_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(FriendStatus), default=FriendStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', foreign_keys=[user_id], back_populates='friends')
    friend = relationship('User', foreign_keys=[friend_id], back_populates='friend_requests')

    def __repr__(self):
        return f'<Friend {self.user.username} -> {self.friend.username} ({self.status.value})>'

# Initialize default guild settings
def init_guild_settings():
    """Initialize default guild settings"""
    settings = {
        'creation_cost_exons': 100000,  # 100k Exons
        'creation_cost_crystals': 50000,  # 50k Crystals
        'max_members_initial': 100,
        'max_members_per_level': 10,  # Additional slots per guild level
        'experience_requirement': {
            'base': 1000,  # Base XP needed for level 1
            'multiplier': 1.5  # XP requirement increases by 50% per level
        }
    }
    
    # Store settings in database or config file
    return settings
