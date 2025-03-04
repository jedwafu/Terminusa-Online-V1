"""
Social models for Terminusa Online
"""
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB

from models import db

class FriendStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"

class PartyRole(Enum):
    LEADER = "leader"
    MEMBER = "member"

class Friend(db.Model):
    __tablename__ = 'friends'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Friendship Status
    status = db.Column(db.Enum(FriendStatus), nullable=False, default=FriendStatus.PENDING)
    
    # Friendship Stats
    gates_cleared_together = db.Column(db.Integer, default=0)
    quests_completed_together = db.Column(db.Integer, default=0)
    trades_completed = db.Column(db.Integer, default=0)
    
    # Privacy Settings
    share_location = db.Column(db.Boolean, default=True)
    share_status = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)

    def accept_request(self) -> Dict:
        """Accept friend request"""
        if self.status != FriendStatus.PENDING:
            return {
                'success': False,
                'message': 'Request is not pending'
            }
            
        self.status = FriendStatus.ACCEPTED
        return {
            'success': True,
            'message': 'Friend request accepted'
        }

    def block_friend(self) -> Dict:
        """Block friend"""
        if self.status == FriendStatus.BLOCKED:
            return {
                'success': False,
                'message': 'Already blocked'
            }
            
        self.status = FriendStatus.BLOCKED
        return {
            'success': True,
            'message': 'Friend blocked'
        }

    def update_interaction(self, interaction_type: str) -> None:
        """Update friendship interaction stats"""
        self.last_interaction = datetime.utcnow()
        
        if interaction_type == 'gate':
            self.gates_cleared_together += 1
        elif interaction_type == 'quest':
            self.quests_completed_together += 1
        elif interaction_type == 'trade':
            self.trades_completed += 1

    def to_dict(self) -> Dict:
        """Convert friend data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'friend_id': self.friend_id,
            'status': self.status.value,
            'stats': {
                'gates_cleared': self.gates_cleared_together,
                'quests_completed': self.quests_completed_together,
                'trades_completed': self.trades_completed
            },
            'privacy': {
                'share_location': self.share_location,
                'share_status': self.share_status
            },
            'timestamps': {
                'created': self.created_at.isoformat(),
                'updated': self.updated_at.isoformat(),
                'last_interaction': self.last_interaction.isoformat()
            }
        }

class BlockedUser(db.Model):
    __tablename__ = 'blocked_users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blocked_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert blocked user data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'blocked_id': self.blocked_id,
            'reason': self.reason,
            'created_at': self.created_at.isoformat()
        }

class Party(db.Model):
    __tablename__ = 'parties'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Party Settings
    name = db.Column(db.String(50), nullable=True)
    max_size = db.Column(db.Integer, default=4)
    min_level = db.Column(db.Integer, default=1)
    is_public = db.Column(db.Boolean, default=True)
    
    # Party Status
    in_gate = db.Column(db.Boolean, default=False)
    gate_id = db.Column(db.Integer, db.ForeignKey('gates.id'), nullable=True)
    
    # Party Settings
    loot_method = db.Column(db.String(20), default='free_for_all')
    exp_share = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    disbanded_at = db.Column(db.DateTime, nullable=True)

    def add_member(self, user_id: int) -> Dict:
        """Add member to party"""
        member = PartyMember.query.filter_by(party_id=self.id).count()
        
        if member >= self.max_size:
            return {
                'success': False,
                'message': 'Party is full'
            }
            
        new_member = PartyMember(
            party_id=self.id,
            user_id=user_id,
            role=PartyRole.MEMBER
        )
        db.session.add(new_member)
        
        return {
            'success': True,
            'message': 'Member added to party'
        }

    def remove_member(self, user_id: int) -> Dict:
        """Remove member from party"""
        member = PartyMember.query.filter_by(
            party_id=self.id,
            user_id=user_id
        ).first()
        
        if not member:
            return {
                'success': False,
                'message': 'Member not found'
            }
            
        db.session.delete(member)
        return {
            'success': True,
            'message': 'Member removed from party'
        }

    def disband(self) -> Dict:
        """Disband the party"""
        self.disbanded_at = datetime.utcnow()
        PartyMember.query.filter_by(party_id=self.id).delete()
        
        return {
            'success': True,
            'message': 'Party disbanded'
        }

    def to_dict(self) -> Dict:
        """Convert party data to dictionary"""
        return {
            'id': self.id,
            'leader_id': self.leader_id,
            'settings': {
                'name': self.name,
                'max_size': self.max_size,
                'min_level': self.min_level,
                'is_public': self.is_public,
                'loot_method': self.loot_method,
                'exp_share': self.exp_share
            },
            'status': {
                'in_gate': self.in_gate,
                'gate_id': self.gate_id
            },
            'timestamps': {
                'created': self.created_at.isoformat(),
                'disbanded': self.disbanded_at.isoformat() if self.disbanded_at else None
            }
        }

class PartyMember(db.Model):
    __tablename__ = 'party_members'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum(PartyRole), nullable=False, default=PartyRole.MEMBER)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert party member data to dictionary"""
        return {
            'id': self.id,
            'party_id': self.party_id,
            'user_id': self.user_id,
            'role': self.role.value,
            'joined_at': self.joined_at.isoformat()
        }
