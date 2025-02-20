"""
Tests for the social systems (guilds, parties, friends).
"""

import pytest
from typing import Dict, Any
from datetime import datetime

def test_guild_creation(test_user: Dict[str, Any], db_session):
    """Test guild creation."""
    from models import Guild
    
    guild = Guild(
        name="Test Guild",
        description="A test guild",
        level=1,
        experience=0,
        creation_cost_exons=100000,
        creation_cost_crystals=50000,
        max_members=100,
        announcement="Welcome to the test guild!",
        created_at=datetime.utcnow()
    )
    
    db_session.add(guild)
    db_session.commit()
    
    assert guild.id is not None
    assert guild.name == "Test Guild"
    assert guild.level == 1

def test_guild_member_management(test_guild: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test guild member management."""
    from models import GuildMember, GuildRank
    
    # Create new member
    member = GuildMember(
        guild_id=test_guild['id'],
        user_id=test_user['id'],
        rank=GuildRank.MEMBER,
        contribution=0,
        joined_at=datetime.utcnow()
    )
    
    db_session.add(member)
    db_session.commit()
    
    assert member.id is not None
    assert member.guild_id == test_guild['id']
    assert member.rank == GuildRank.MEMBER

def test_party_creation(test_user: Dict[str, Any], db_session):
    """Test party creation."""
    from models import Party
    
    party = Party(
        name="Test Party",
        leader_id=test_user['id'],
        is_active=True,
        level_range=10,
        auto_loot_distribution=True,
        loot_quality_threshold='BASIC',
        created_at=datetime.utcnow()
    )
    
    db_session.add(party)
    db_session.commit()
    
    assert party.id is not None
    assert party.name == "Test Party"
    assert party.leader_id == test_user['id']

def test_party_member_management(test_party: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test party member management."""
    from models import PartyMember, PartyRole
    
    # Create new member
    member = PartyMember(
        party_id=test_party['id'],
        user_id=test_user['id'],
        role=PartyRole.MEMBER,
        joined_at=datetime.utcnow()
    )
    
    db_session.add(member)
    db_session.commit()
    
    assert member.id is not None
    assert member.party_id == test_party['id']
    assert member.role == PartyRole.MEMBER

def test_friend_system(test_user: Dict[str, Any], db_session):
    """Test friend system."""
    from models import Friend, FriendStatus, User
    
    # Create another user
    friend_user = User(
        username='frienduser',
        email='friend@example.com',
        role='player'
    )
    friend_user.set_password('testpass123')
    db_session.add(friend_user)
    db_session.commit()
    
    # Create friend request
    friend = Friend(
        user_id=test_user['id'],
        friend_id=friend_user.id,
        status=FriendStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    db_session.add(friend)
    db_session.commit()
    
    assert friend.id is not None
    assert friend.status == FriendStatus.PENDING

def test_guild_rank_permissions(test_guild: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test guild rank permissions."""
    from models import GuildMember, GuildRank
    
    # Create members with different ranks
    ranks = {
        GuildRank.MASTER: True,
        GuildRank.VICE_MASTER: True,
        GuildRank.ELDER: True,
        GuildRank.VETERAN: False,
        GuildRank.MEMBER: False,
        GuildRank.RECRUIT: False
    }
    
    for rank, can_manage in ranks.items():
        member = GuildMember(
            guild_id=test_guild['id'],
            user_id=test_user['id'],
            rank=rank
        )
        db_session.add(member)
        db_session.commit()
        
        assert member.can_manage_members() == can_manage

def test_party_reward_sharing(test_party: Dict[str, Any], db_session):
    """Test party reward sharing."""
    from models import Party
    
    party = Party.query.get(test_party['id'])
    
    # Test reward sharing with different party sizes
    rewards = {
        1: 1000.0,  # Solo
        2: 900.0,   # 2 members (10% reduction)
        3: 810.0,   # 3 members (additional 10% reduction)
        4: 729.0    # 4 members (additional 10% reduction)
    }
    
    for size, expected_share in rewards.items():
        total_reward = 1000.0 * size  # Total reward scales with party size
        share = party.calculate_rewards_share(total_reward)
        assert abs(share - expected_share) < 0.01  # Account for floating point

def test_guild_experience_system(test_guild: Dict[str, Any], db_session):
    """Test guild experience system."""
    from models import Guild
    
    guild = Guild.query.get(test_guild['id'])
    initial_level = guild.level
    
    # Add experience
    guild.experience += 10000
    db_session.commit()
    
    assert guild.level > initial_level

def test_party_level_range_validation(test_party: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test party level range validation."""
    from models import Party, PartyMember, User, PlayerCharacter
    
    # Create high level character
    high_level_user = User(username='highlevel', email='high@example.com', role='player')
    high_level_user.set_password('testpass123')
    db_session.add(high_level_user)
    db_session.commit()
    
    high_level_char = PlayerCharacter(
        user_id=high_level_user.id,
        name="High Level",
        level=50
    )
    db_session.add(high_level_char)
    db_session.commit()
    
    party = Party.query.get(test_party['id'])
    
    # Try to add high level member to low level party
    with pytest.raises(ValueError):
        member = PartyMember(
            party_id=party.id,
            user_id=high_level_user.id
        )
        db_session.add(member)
        db_session.commit()

def test_guild_announcement_system(test_guild: Dict[str, Any], db_session):
    """Test guild announcement system."""
    from models import Guild
    
    guild = Guild.query.get(test_guild['id'])
    
    # Update announcement
    new_announcement = "Important guild announcement!"
    guild.announcement = new_announcement
    db_session.commit()
    
    assert guild.announcement == new_announcement

def test_friend_status_transitions(test_user: Dict[str, Any], db_session):
    """Test friend status transitions."""
    from models import Friend, FriendStatus, User
    
    # Create another user
    other_user = User(username='other', email='other@example.com', role='player')
    other_user.set_password('testpass123')
    db_session.add(other_user)
    db_session.commit()
    
    # Create friend request
    friend = Friend(
        user_id=test_user['id'],
        friend_id=other_user.id,
        status=FriendStatus.PENDING
    )
    db_session.add(friend)
    db_session.commit()
    
    # Test valid transitions
    valid_transitions = [
        (FriendStatus.PENDING, FriendStatus.ACCEPTED),
        (FriendStatus.ACCEPTED, FriendStatus.BLOCKED),
        (FriendStatus.BLOCKED, FriendStatus.ACCEPTED)
    ]
    
    for from_status, to_status in valid_transitions:
        friend.status = from_status
        db_session.commit()
        
        friend.status = to_status
        db_session.commit()
        
        assert friend.status == to_status
