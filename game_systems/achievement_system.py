from typing import Dict, List, Optional
from datetime import datetime
import random

from models import db, Guild, GuildAchievement, GuildMember, User
from game_systems.event_system import EventSystem, EventType, GameEvent

class AchievementSystem:
    def __init__(self, websocket):
        self.event_system = EventSystem(websocket)
        self.achievement_definitions = {
            # Member Milestones
            'growing_family': {
                'name': 'Growing Family',
                'description': 'Reach {target} active guild members',
                'type': 'member_count',
                'tiers': [
                    {'target': 10, 'rewards': {'crystals': 1000, 'exons': 10}},
                    {'target': 25, 'rewards': {'crystals': 2500, 'exons': 25}},
                    {'target': 50, 'rewards': {'crystals': 5000, 'exons': 50}}
                ]
            },
            
            # Gate Clearing
            'gate_masters': {
                'name': 'Gate Masters',
                'description': 'Clear {target} gates as a guild',
                'type': 'gates_cleared',
                'tiers': [
                    {'target': 100, 'rewards': {'crystals': 2000, 'exons': 20}},
                    {'target': 500, 'rewards': {'crystals': 10000, 'exons': 100}},
                    {'target': 1000, 'rewards': {'crystals': 20000, 'exons': 200}}
                ]
            },
            
            # Guild Level
            'guild_ascension': {
                'name': 'Guild Ascension',
                'description': 'Reach guild level {target}',
                'type': 'guild_level',
                'tiers': [
                    {'target': 10, 'rewards': {'crystals': 5000, 'exons': 50}},
                    {'target': 25, 'rewards': {'crystals': 12500, 'exons': 125}},
                    {'target': 50, 'rewards': {'crystals': 25000, 'exons': 250}}
                ]
            },
            
            # Quest Completion
            'quest_champions': {
                'name': 'Quest Champions',
                'description': 'Complete {target} guild quests',
                'type': 'quests_completed',
                'tiers': [
                    {'target': 50, 'rewards': {'crystals': 3000, 'exons': 30}},
                    {'target': 200, 'rewards': {'crystals': 12000, 'exons': 120}},
                    {'target': 500, 'rewards': {'crystals': 30000, 'exons': 300}}
                ]
            },
            
            # Treasury Growth
            'wealthy_guild': {
                'name': 'Wealthy Guild',
                'description': 'Accumulate {target} crystals in guild treasury',
                'type': 'crystal_balance',
                'tiers': [
                    {'target': 100000, 'rewards': {'crystals': 10000, 'exons': 100}},
                    {'target': 500000, 'rewards': {'crystals': 50000, 'exons': 500}},
                    {'target': 1000000, 'rewards': {'crystals': 100000, 'exons': 1000}}
                ]
            },
            
            # High Level Members
            'elite_force': {
                'name': 'Elite Force',
                'description': 'Have {target} members reach level 50+',
                'type': 'high_level_members',
                'tiers': [
                    {'target': 5, 'rewards': {'crystals': 5000, 'exons': 50}},
                    {'target': 15, 'rewards': {'crystals': 15000, 'exons': 150}},
                    {'target': 30, 'rewards': {'crystals': 30000, 'exons': 300}}
                ]
            }
        }

    def initialize_guild_achievements(self, guild: Guild) -> None:
        """Initialize achievements for a new guild"""
        try:
            for achievement_id, definition in self.achievement_definitions.items():
                # Create first tier achievement
                first_tier = definition['tiers'][0]
                achievement = GuildAchievement(
                    guild_id=guild.id,
                    name=definition['name'],
                    description=definition['description'].format(target=first_tier['target']),
                    requirements={
                        'type': definition['type'],
                        'target': first_tier['target']
                    },
                    rewards=first_tier['rewards'],
                    target=first_tier['target'],
                    progress=0
                )
                db.session.add(achievement)
            
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to initialize guild achievements: {str(e)}")

    def check_achievements(self, guild: Guild, trigger_type: str, value: int = None) -> None:
        """Check and update achievements based on trigger"""
        try:
            achievements = GuildAchievement.query.filter_by(
                guild_id=guild.id,
                completed=False
            ).all()

            for achievement in achievements:
                if achievement.requirements['type'] != trigger_type:
                    continue

                # Update progress based on trigger type
                if trigger_type == 'member_count':
                    progress = len(guild.active_members)
                elif trigger_type == 'gates_cleared':
                    progress = guild.total_gates_cleared
                elif trigger_type == 'guild_level':
                    progress = guild.level
                elif trigger_type == 'quests_completed':
                    progress = guild.quests.filter_by(status='completed').count()
                elif trigger_type == 'crystal_balance':
                    progress = int(guild.crystal_balance)
                elif trigger_type == 'high_level_members':
                    progress = sum(1 for m in guild.active_members if m.user.level >= 50)
                else:
                    continue

                # Update achievement progress
                achievement.progress = progress
                
                # Check if achievement is completed
                if progress >= achievement.target:
                    self._complete_achievement(achievement, guild)
                    
                    # Create next tier achievement if available
                    self._create_next_tier_achievement(achievement, guild)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to check achievements: {str(e)}")

    def _complete_achievement(self, achievement: GuildAchievement, guild: Guild) -> None:
        """Complete an achievement and grant rewards"""
        try:
            achievement.completed = True
            achievement.completed_at = datetime.utcnow()

            # Grant rewards
            if 'crystals' in achievement.rewards:
                guild.crystal_balance += achievement.rewards['crystals']
            if 'exons' in achievement.rewards:
                guild.exon_balance += achievement.rewards['exons']

            # Emit achievement completion event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=guild.id,
                data={
                    'type': 'achievement_completed',
                    'achievement': achievement.to_dict(),
                    'rewards': achievement.rewards
                }
            ))

        except Exception as e:
            raise Exception(f"Failed to complete achievement: {str(e)}")

    def _create_next_tier_achievement(self, completed_achievement: GuildAchievement, guild: Guild) -> None:
        """Create next tier achievement if available"""
        try:
            # Find achievement definition
            for achievement_id, definition in self.achievement_definitions.items():
                if definition['name'] == completed_achievement.name:
                    # Find current tier index
                    current_target = completed_achievement.target
                    current_tier_index = next(
                        (i for i, tier in enumerate(definition['tiers']) 
                         if tier['target'] == current_target),
                        -1
                    )

                    # Check if next tier exists
                    if current_tier_index < len(definition['tiers']) - 1:
                        next_tier = definition['tiers'][current_tier_index + 1]
                        
                        # Create next tier achievement
                        new_achievement = GuildAchievement(
                            guild_id=guild.id,
                            name=definition['name'],
                            description=definition['description'].format(target=next_tier['target']),
                            requirements={
                                'type': definition['type'],
                                'target': next_tier['target']
                            },
                            rewards=next_tier['rewards'],
                            target=next_tier['target'],
                            progress=completed_achievement.progress
                        )
                        db.session.add(new_achievement)
                        
                        # Emit new achievement event
                        self.event_system.emit_event(GameEvent(
                            type=EventType.GUILD_UPDATE,
                            guild_id=guild.id,
                            data={
                                'type': 'achievement_unlocked',
                                'achievement': new_achievement.to_dict()
                            }
                        ))
                        
                    break

        except Exception as e:
            raise Exception(f"Failed to create next tier achievement: {str(e)}")
