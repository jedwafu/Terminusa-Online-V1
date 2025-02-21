from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

from models import db, Guild, GuildQuest, GuildMember, User
from models.guild import QuestDifficulty, QuestStatus
from game_systems.event_system import EventSystem, EventType, GameEvent

class QuestSystem:
    def __init__(self, websocket):
        self.event_system = EventSystem(websocket)

    def generate_quest(self, guild: Guild, difficulty: Optional[str] = None) -> GuildQuest:
        """Generate a new AI-powered guild quest based on guild stats and activity"""
        if not difficulty:
            difficulty = guild.settings.get('quest_difficulty', 'normal')

        # Get guild stats for quest generation
        avg_level = guild.average_level
        active_members = len(guild.active_members)
        total_gates = guild.total_gates_cleared

        # Generate quest parameters based on difficulty
        quest_params = self._calculate_quest_parameters(
            difficulty=difficulty,
            avg_level=avg_level,
            active_members=active_members,
            total_gates=total_gates
        )

        # Create quest
        quest = GuildQuest(
            guild_id=guild.id,
            title=quest_params['title'],
            description=quest_params['description'],
            difficulty=difficulty,
            requirements=quest_params['requirements'],
            rewards=quest_params['rewards'],
            target=quest_params['target'],
            participants={}
        )

        db.session.add(quest)
        db.session.commit()

        # Emit quest creation event
        self.event_system.emit_event(GameEvent(
            type=EventType.GUILD_UPDATE,
            guild_id=guild.id,
            data={
                'type': 'quest_created',
                'quest': quest.to_dict()
            }
        ))

        return quest

    def _calculate_quest_parameters(self, difficulty: str, avg_level: float, 
                                 active_members: int, total_gates: int) -> Dict:
        """Calculate quest parameters based on guild stats"""
        # Base multipliers for different difficulties
        difficulty_multipliers = {
            'normal': 1.0,
            'hard': 1.5,
            'extreme': 2.0
        }
        multiplier = difficulty_multipliers[difficulty]

        # Quest types and their base requirements/rewards
        quest_types = [
            {
                'type': 'gate_clear',
                'title_template': '{rank} Gate Clearing Quest',
                'description_template': 'Clear {count} {rank} rank gates as a guild.',
                'base_target': 5,
                'base_rewards': {
                    'crystals': 1000,
                    'exons': 10
                }
            },
            {
                'type': 'monster_hunt',
                'title_template': 'Hunt {monster_type} Beasts',
                'description_template': 'Defeat {count} {monster_type} magic beasts in gates.',
                'base_target': 20,
                'base_rewards': {
                    'crystals': 800,
                    'exons': 8
                }
            },
            {
                'type': 'guild_exp',
                'title_template': 'Guild Growth Quest',
                'description_template': 'Earn {count} guild experience points.',
                'base_target': 1000,
                'base_rewards': {
                    'crystals': 1200,
                    'exons': 12
                }
            }
        ]

        # Select random quest type
        quest_type = random.choice(quest_types)

        # Calculate target based on guild stats
        base_target = quest_type['base_target']
        level_factor = avg_level / 10
        member_factor = active_members / 5
        adjusted_target = int(base_target * multiplier * (level_factor + member_factor))

        # Calculate rewards
        base_rewards = quest_type['base_rewards']
        adjusted_rewards = {
            currency: int(amount * multiplier * (level_factor + member_factor))
            for currency, amount in base_rewards.items()
        }

        # Generate quest content based on type
        if quest_type['type'] == 'gate_clear':
            rank = self._determine_gate_rank(avg_level)
            title = quest_type['title_template'].format(rank=rank)
            description = quest_type['description_template'].format(
                count=adjusted_target,
                rank=rank
            )
            requirements = {
                'type': 'gate_clear',
                'rank': rank,
                'count': adjusted_target
            }

        elif quest_type['type'] == 'monster_hunt':
            monster_type = self._determine_monster_type(avg_level)
            title = quest_type['title_template'].format(monster_type=monster_type)
            description = quest_type['description_template'].format(
                count=adjusted_target,
                monster_type=monster_type.lower()
            )
            requirements = {
                'type': 'monster_hunt',
                'monster_type': monster_type,
                'count': adjusted_target
            }

        else:  # guild_exp
            title = quest_type['title_template']
            description = quest_type['description_template'].format(
                count=adjusted_target
            )
            requirements = {
                'type': 'guild_exp',
                'count': adjusted_target
            }

        return {
            'title': title,
            'description': description,
            'requirements': requirements,
            'rewards': adjusted_rewards,
            'target': adjusted_target
        }

    def _determine_gate_rank(self, avg_level: float) -> str:
        """Determine appropriate gate rank based on average level"""
        if avg_level >= 80:
            return random.choice(['S', 'A'])
        elif avg_level >= 60:
            return random.choice(['A', 'B'])
        elif avg_level >= 40:
            return random.choice(['B', 'C'])
        elif avg_level >= 20:
            return random.choice(['C', 'D'])
        else:
            return random.choice(['D', 'E'])

    def _determine_monster_type(self, avg_level: float) -> str:
        """Determine appropriate monster type based on average level"""
        monster_types = [
            'Shadow', 'Frost', 'Flame', 'Storm', 'Earth',
            'Void', 'Light', 'Dark', 'Chaos', 'Ancient'
        ]
        # Higher levels get more challenging monster types
        index = min(int(avg_level / 10), len(monster_types) - 1)
        return random.choice(monster_types[max(0, index-2):index+1])

    def update_quest_progress(self, quest: GuildQuest, user: User, 
                            progress_type: str, amount: int = 1) -> None:
        """Update quest progress for a user"""
        try:
            if quest.status != QuestStatus.ACTIVE.value:
                return

            # Update participant progress
            participants = quest.participants or {}
            user_progress = participants.get(str(user.id), 0)
            participants[str(user.id)] = user_progress + amount
            quest.participants = participants

            # Calculate total progress
            total_progress = sum(participants.values())
            quest.progress = total_progress

            # Check if quest is completed
            if total_progress >= quest.target:
                self._complete_quest(quest, user)
            else:
                db.session.commit()

                # Emit progress update event
                self.event_system.emit_event(GameEvent(
                    type=EventType.GUILD_UPDATE,
                    guild_id=quest.guild_id,
                    data={
                        'type': 'quest_progress',
                        'quest_id': quest.id,
                        'progress': quest.progress,
                        'target': quest.target,
                        'participants': quest.participants
                    }
                ))

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to update quest progress: {str(e)}")

    def _complete_quest(self, quest: GuildQuest, completed_by: User) -> None:
        """Complete a guild quest and distribute rewards"""
        try:
            quest.status = QuestStatus.COMPLETED.value
            quest.completed_at = datetime.utcnow()
            quest.completed_by = completed_by.id

            # Get guild and process rewards
            guild = Guild.query.get(quest.guild_id)
            if guild:
                # Add rewards to guild treasury
                if 'crystals' in quest.rewards:
                    guild.crystal_balance += quest.rewards['crystals']
                if 'exons' in quest.rewards:
                    guild.exon_balance += quest.rewards['exons']

            db.session.commit()

            # Emit quest completion event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=quest.guild_id,
                data={
                    'type': 'quest_completed',
                    'quest': quest.to_dict(),
                    'completed_by': completed_by.username,
                    'rewards': quest.rewards
                }
            ))

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to complete quest: {str(e)}")

    def check_expired_quests(self) -> None:
        """Check and expire old quests"""
        try:
            # Find quests that are more than 24 hours old
            expired_time = datetime.utcnow() - timedelta(hours=24)
            expired_quests = GuildQuest.query.filter(
                GuildQuest.status == QuestStatus.ACTIVE.value,
                GuildQuest.started_at < expired_time
            ).all()

            for quest in expired_quests:
                quest.status = QuestStatus.FAILED.value
                
                # Emit quest expired event
                self.event_system.emit_event(GameEvent(
                    type=EventType.GUILD_UPDATE,
                    guild_id=quest.guild_id,
                    data={
                        'type': 'quest_expired',
                        'quest_id': quest.id
                    }
                ))

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to check expired quests: {str(e)}")
