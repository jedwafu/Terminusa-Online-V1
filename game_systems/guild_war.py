from typing import Dict, List, Optional
from datetime import datetime, timedelta
import random

from models import db, Guild, GuildMember, User
from game_systems.event_system import EventSystem, EventType, GameEvent
from game_systems.achievement_triggers import AchievementTriggers

class GuildWar:
    def __init__(self, websocket):
        self.event_system = EventSystem(websocket)
        self.achievement_triggers = AchievementTriggers(websocket)

        # War status constants
        self.WAR_PREPARATION_TIME = timedelta(hours=24)
        self.WAR_DURATION = timedelta(hours=48)
        self.MIN_PARTICIPANTS = 10
        self.MAX_PARTICIPANTS = 50

        # Point system
        self.POINTS = {
            'kill': 10,
            'gate_capture': 50,
            'territory_hold': 5,  # per hour
            'boss_kill': 100
        }

    def initiate_war(self, challenger: Guild, target: Guild) -> Dict:
        """Initiate a guild war challenge"""
        try:
            if challenger.id == target.id:
                return {
                    "success": False,
                    "message": "Cannot declare war on your own guild"
                }

            if challenger.level < 10 or target.level < 10:
                return {
                    "success": False,
                    "message": "Both guilds must be at least level 10"
                }

            if len(challenger.active_members) < self.MIN_PARTICIPANTS:
                return {
                    "success": False,
                    "message": f"Challenging guild must have at least {self.MIN_PARTICIPANTS} active members"
                }

            # Create war record
            war_data = {
                'challenger_id': challenger.id,
                'target_id': target.id,
                'status': 'pending',
                'start_time': datetime.utcnow() + self.WAR_PREPARATION_TIME,
                'end_time': datetime.utcnow() + self.WAR_PREPARATION_TIME + self.WAR_DURATION,
                'participants': {
                    str(challenger.id): [],
                    str(target.id): []
                },
                'scores': {
                    str(challenger.id): 0,
                    str(target.id): 0
                },
                'territories': {},
                'events': []
            }

            # Store war data
            self._save_war_data(war_data)

            # Emit war declaration event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=challenger.id,
                data={
                    'type': 'war_declared',
                    'challenger': challenger.name,
                    'target': target.name,
                    'preparation_time': str(self.WAR_PREPARATION_TIME),
                    'war_duration': str(self.WAR_DURATION)
                }
            ))

            return {
                "success": True,
                "message": f"War declared against {target.name}",
                "war_data": war_data
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to initiate war: {str(e)}"
            }

    def register_participants(self, guild: Guild, member_ids: List[int], war_id: str) -> Dict:
        """Register guild members for war participation"""
        try:
            war_data = self._get_war_data(war_id)
            if not war_data:
                return {
                    "success": False,
                    "message": "War not found"
                }

            if war_data['status'] != 'pending':
                return {
                    "success": False,
                    "message": "Registration period has ended"
                }

            # Validate participants
            valid_members = []
            for member_id in member_ids:
                member = GuildMember.query.filter_by(
                    user_id=member_id,
                    guild_id=guild.id,
                    active=True
                ).first()
                
                if member and member.user.level >= 30:  # Minimum level requirement
                    valid_members.append(member_id)

            if len(valid_members) > self.MAX_PARTICIPANTS:
                return {
                    "success": False,
                    "message": f"Maximum {self.MAX_PARTICIPANTS} participants allowed"
                }

            # Update war participants
            war_data['participants'][str(guild.id)] = valid_members
            self._save_war_data(war_data)

            return {
                "success": True,
                "message": f"Registered {len(valid_members)} participants",
                "participants": valid_members
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to register participants: {str(e)}"
            }

    def process_combat_event(self, war_id: str, event_data: Dict) -> Dict:
        """Process a combat event during war"""
        try:
            war_data = self._get_war_data(war_id)
            if not war_data or war_data['status'] != 'active':
                return {
                    "success": False,
                    "message": "Invalid war or war not active"
                }

            event_type = event_data.get('type')
            attacker_guild_id = event_data.get('attacker_guild_id')
            points = 0

            # Calculate points based on event type
            if event_type == 'kill':
                points = self.POINTS['kill']
            elif event_type == 'gate_capture':
                points = self.POINTS['gate_capture']
            elif event_type == 'boss_kill':
                points = self.POINTS['boss_kill']

            # Update scores
            if points > 0:
                war_data['scores'][str(attacker_guild_id)] += points

            # Record event
            event_data['timestamp'] = datetime.utcnow().isoformat()
            event_data['points'] = points
            war_data['events'].append(event_data)

            # Update war data
            self._save_war_data(war_data)

            # Emit combat event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                data={
                    'type': 'war_combat_event',
                    'war_id': war_id,
                    'event': event_data,
                    'scores': war_data['scores']
                }
            ))

            return {
                "success": True,
                "message": "Combat event processed",
                "points_awarded": points
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to process combat event: {str(e)}"
            }

    def end_war(self, war_id: str) -> Dict:
        """End a guild war and determine winner"""
        try:
            war_data = self._get_war_data(war_id)
            if not war_data:
                return {
                    "success": False,
                    "message": "War not found"
                }

            # Determine winner
            challenger_id = war_data['challenger_id']
            target_id = war_data['target_id']
            challenger_score = war_data['scores'][str(challenger_id)]
            target_score = war_data['scores'][str(target_id)]

            winner_id = challenger_id if challenger_score > target_score else target_id
            winner_guild = Guild.query.get(winner_id)

            # Calculate rewards
            rewards = self._calculate_war_rewards(war_data, winner_id)

            # Update war data
            war_data['status'] = 'completed'
            war_data['winner_id'] = winner_id
            war_data['rewards'] = rewards
            self._save_war_data(war_data)

            # Distribute rewards
            self._distribute_rewards(winner_guild, rewards)

            # Trigger achievements
            self.achievement_triggers.handle_special_event(winner_guild, {
                'type': 'guild_war',
                'result': 'victory'
            })

            # Emit war end event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                data={
                    'type': 'war_ended',
                    'war_id': war_id,
                    'winner': winner_guild.name,
                    'final_scores': war_data['scores'],
                    'rewards': rewards
                }
            ))

            return {
                "success": True,
                "message": f"War ended. Winner: {winner_guild.name}",
                "war_data": war_data
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to end war: {str(e)}"
            }

    def _calculate_war_rewards(self, war_data: Dict, winner_id: int) -> Dict:
        """Calculate rewards for war victory"""
        base_rewards = {
            'crystals': 50000,
            'exons': 500,
            'guild_exp': 5000
        }

        # Scale rewards based on war intensity
        total_events = len(war_data['events'])
        intensity_multiplier = min(2.0, 1.0 + (total_events / 1000))

        return {
            'crystals': int(base_rewards['crystals'] * intensity_multiplier),
            'exons': int(base_rewards['exons'] * intensity_multiplier),
            'guild_exp': int(base_rewards['guild_exp'] * intensity_multiplier)
        }

    def _distribute_rewards(self, guild: Guild, rewards: Dict) -> None:
        """Distribute war rewards to winning guild"""
        try:
            # Add rewards to guild treasury
            guild.crystal_balance += rewards['crystals']
            guild.exon_balance += rewards['exons']
            
            # Add guild experience
            from game_systems.progression_system import ProgressionSystem
            progression_system = ProgressionSystem(self.event_system.websocket)
            progression_system.add_experience(
                guild=guild,
                amount=rewards['guild_exp'],
                source='guild_war_victory'
            )

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to distribute rewards: {str(e)}")

    def _get_war_data(self, war_id: str) -> Optional[Dict]:
        """Get war data from storage"""
        # Implementation would depend on your storage solution
        # This could be in Redis, database, etc.
        pass

    def _save_war_data(self, war_data: Dict) -> None:
        """Save war data to storage"""
        # Implementation would depend on your storage solution
        # This could be in Redis, database, etc.
        pass
