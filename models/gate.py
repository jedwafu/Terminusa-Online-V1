"""
Gate model for Terminusa Online
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB

from models import db

class GateType(Enum):
    NORMAL = "normal"
    ELITE = "elite"
    BOSS = "boss"
    EVENT = "event"
    RAID = "raid"

class GateStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLEARED = "cleared"
    FAILED = "failed"
    EXPIRED = "expired"

class GateRank(Enum):
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"
    SS = "SS"

class Gate(db.Model):
    __tablename__ = 'gates'

    id = db.Column(db.Integer, primary_key=True)
    
    # Gate Info
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    type = db.Column(db.Enum(GateType), nullable=False)
    rank = db.Column(db.Enum(GateRank), nullable=False)
    level_requirement = db.Column(db.Integer, nullable=False)
    
    # Gate Status
    status = db.Column(db.Enum(GateStatus), nullable=False, default=GateStatus.OPEN)
    current_party = db.Column(JSONB, nullable=True)
    party_size_min = db.Column(db.Integer, default=1)
    party_size_max = db.Column(db.Integer, default=4)
    
    # Gate Configuration
    difficulty = db.Column(db.Float, nullable=False)  # 1.0 = normal
    time_limit = db.Column(db.Integer, nullable=True)  # seconds
    entry_cost = db.Column(JSONB, nullable=False, default={})
    
    # Gate Content
    monsters = db.Column(JSONB, nullable=False, default=[])
    bosses = db.Column(JSONB, nullable=False, default=[])
    traps = db.Column(JSONB, nullable=False, default=[])
    treasures = db.Column(JSONB, nullable=False, default=[])
    
    # Gate Progress
    current_floor = db.Column(db.Integer, default=1)
    total_floors = db.Column(db.Integer, nullable=False)
    cleared_floors = db.Column(JSONB, nullable=False, default=[])
    
    # Gate Rewards
    base_rewards = db.Column(JSONB, nullable=False, default={})
    bonus_conditions = db.Column(JSONB, nullable=False, default=[])
    achieved_conditions = db.Column(JSONB, nullable=False, default=[])
    
    # Gate Statistics
    total_attempts = db.Column(db.Integer, default=0)
    total_clears = db.Column(db.Integer, default=0)
    fastest_clear = db.Column(db.Integer, nullable=True)  # seconds
    highest_score = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, name: str, description: str, type: GateType, 
                 rank: GateRank, level_requirement: int, total_floors: int,
                 difficulty: float = 1.0):
        self.name = name
        self.description = description
        self.type = type
        self.rank = rank
        self.level_requirement = level_requirement
        self.total_floors = total_floors
        self.difficulty = difficulty

    def start_gate(self, party: List[Dict]) -> Dict:
        """Start the gate with a party"""
        if self.status != GateStatus.OPEN:
            return {
                'success': False,
                'message': 'Gate is not available'
            }
            
        if len(party) < self.party_size_min or len(party) > self.party_size_max:
            return {
                'success': False,
                'message': f'Party size must be between {self.party_size_min} and {self.party_size_max}'
            }
            
        # Check level requirements
        for member in party:
            if member['level'] < self.level_requirement:
                return {
                    'success': False,
                    'message': f'All party members must be level {self.level_requirement} or higher'
                }
        
        self.status = GateStatus.IN_PROGRESS
        self.current_party = party
        self.started_at = datetime.utcnow()
        self.total_attempts += 1
        
        return {
            'success': True,
            'message': 'Gate started successfully',
            'gate_data': self.get_current_floor_data()
        }

    def process_floor_clear(self, floor_data: Dict) -> Dict:
        """Process floor completion"""
        if self.status != GateStatus.IN_PROGRESS:
            return {
                'success': False,
                'message': 'Gate is not in progress'
            }
            
        if self.current_floor > self.total_floors:
            return {
                'success': False,
                'message': 'All floors already cleared'
            }
            
        # Record floor clear
        self.cleared_floors.append({
            'floor': self.current_floor,
            'time': floor_data.get('clear_time'),
            'score': floor_data.get('score'),
            'conditions': floor_data.get('conditions', [])
        })
        
        # Update progress
        self.current_floor += 1
        
        # Check if gate is completed
        if self.current_floor > self.total_floors:
            return self.complete_gate(floor_data.get('final_score', 0))
            
        return {
            'success': True,
            'message': 'Floor cleared',
            'next_floor': self.get_current_floor_data()
        }

    def complete_gate(self, final_score: int) -> Dict:
        """Complete the gate"""
        self.status = GateStatus.CLEARED
        self.completed_at = datetime.utcnow()
        self.total_clears += 1
        
        # Update records
        clear_time = int((self.completed_at - self.started_at).total_seconds())
        if not self.fastest_clear or clear_time < self.fastest_clear:
            self.fastest_clear = clear_time
            
        if final_score > self.highest_score:
            self.highest_score = final_score
        
        # Calculate rewards
        rewards = self.calculate_rewards(final_score)
        
        return {
            'success': True,
            'message': 'Gate completed successfully',
            'clear_time': clear_time,
            'final_score': final_score,
            'rewards': rewards
        }

    def fail_gate(self, reason: str) -> Dict:
        """Fail the gate"""
        self.status = GateStatus.FAILED
        self.completed_at = datetime.utcnow()
        
        return {
            'success': True,
            'message': 'Gate failed',
            'reason': reason,
            'progress': {
                'floors_cleared': len(self.cleared_floors),
                'current_floor': self.current_floor
            }
        }

    def calculate_rewards(self, score: int) -> Dict:
        """Calculate gate rewards based on performance"""
        rewards = self.base_rewards.copy()
        
        # Apply rank multiplier
        rank_multipliers = {
            GateRank.E: 1.0,
            GateRank.D: 1.2,
            GateRank.C: 1.5,
            GateRank.B: 1.8,
            GateRank.A: 2.2,
            GateRank.S: 2.8,
            GateRank.SS: 3.5
        }
        multiplier = rank_multipliers[self.rank]
        
        # Apply score bonus
        score_bonus = 1.0 + (score / 10000)  # Example: 10000 points = 2x multiplier
        
        # Apply difficulty bonus
        difficulty_bonus = self.difficulty
        
        # Calculate final rewards
        for reward_type, amount in rewards.items():
            if isinstance(amount, (int, float)):
                rewards[reward_type] = int(amount * multiplier * score_bonus * difficulty_bonus)
        
        # Add bonus rewards from achieved conditions
        for condition in self.achieved_conditions:
            if 'rewards' in condition:
                for reward_type, amount in condition['rewards'].items():
                    if reward_type in rewards:
                        rewards[reward_type] += amount
                    else:
                        rewards[reward_type] = amount
        
        return rewards

    def get_current_floor_data(self) -> Dict:
        """Get data for current floor"""
        floor_index = self.current_floor - 1
        
        return {
            'floor_number': self.current_floor,
            'monsters': self.monsters[floor_index] if floor_index < len(self.monsters) else [],
            'bosses': self.bosses[floor_index] if floor_index < len(self.bosses) else [],
            'traps': self.traps[floor_index] if floor_index < len(self.traps) else [],
            'treasures': self.treasures[floor_index] if floor_index < len(self.treasures) else []
        }

    def check_expiry(self) -> bool:
        """Check if gate has expired"""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.status = GateStatus.EXPIRED
            return True
        return False

    def to_dict(self) -> Dict:
        """Convert gate data to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            'rank': self.rank.value,
            'level_requirement': self.level_requirement,
            'status': self.status.value,
            'configuration': {
                'difficulty': self.difficulty,
                'time_limit': self.time_limit,
                'entry_cost': self.entry_cost,
                'party_size': {
                    'min': self.party_size_min,
                    'max': self.party_size_max
                }
            },
            'progress': {
                'current_floor': self.current_floor,
                'total_floors': self.total_floors,
                'cleared_floors': self.cleared_floors
            },
            'rewards': {
                'base_rewards': self.base_rewards,
                'bonus_conditions': self.bonus_conditions,
                'achieved_conditions': self.achieved_conditions
            },
            'statistics': {
                'total_attempts': self.total_attempts,
                'total_clears': self.total_clears,
                'fastest_clear': self.fastest_clear,
                'highest_score': self.highest_score
            },
            'timestamps': {
                'created': self.created_at.isoformat(),
                'started': self.started_at.isoformat() if self.started_at else None,
                'completed': self.completed_at.isoformat() if self.completed_at else None,
                'expires': self.expires_at.isoformat() if self.expires_at else None
            }
        }

    @classmethod
    def generate_gate(cls, player_level: int, player_data: Dict) -> 'Gate':
        """Generate a gate based on player data"""
        from game_systems.ai_agent import AIAgent
        
        ai = AIAgent()
        gate_config = ai.generate_content(player_data)
        
        gate = cls(
            name=gate_config['name'],
            description=gate_config['description'],
            type=GateType[gate_config['type'].upper()],
            rank=GateRank[gate_config['rank']],
            level_requirement=max(1, player_level - 5),
            total_floors=gate_config['total_floors'],
            difficulty=gate_config['difficulty']
        )
        
        gate.monsters = gate_config['monsters']
        gate.bosses = gate_config['bosses']
        gate.traps = gate_config['traps']
        gate.treasures = gate_config['treasures']
        gate.base_rewards = gate_config['rewards']
        gate.bonus_conditions = gate_config['bonus_conditions']
        
        return gate
