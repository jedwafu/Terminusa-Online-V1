from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from models import db, User, Guild, GuildMember, GuildQuest, GuildTransaction
from game_systems.event_system import EventSystem, EventType, GameEvent

class GuildSystem:
    def __init__(self, websocket):
        self.event_system = EventSystem(websocket)

    def create_guild(self, leader: User, name: str, description: str) -> Dict:
        """Create a new guild"""
        try:
            # Check if user already in a guild
            if leader.guild_id:
                return {
                    "success": False,
                    "message": "Already in a guild"
                }

            # Create guild
            guild = Guild(
                name=name,
                description=description,
                leader_id=leader.id,
                level=1,
                crystal_balance=0,
                exon_balance=0,
                crystal_tax_rate=10,  # Default 10%
                exon_tax_rate=10,     # Default 10%
                max_members=50,        # Default max members
                recruitment_status='open'
            )
            db.session.add(guild)
            
            # Add leader as member
            member = GuildMember(
                user_id=leader.id,
                guild_id=guild.id,
                rank='leader',
                joined_at=datetime.utcnow()
            )
            db.session.add(member)
            
            # Update user
            leader.guild_id = guild.id
            
            db.session.commit()

            # Emit guild creation event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                user_id=leader.id,
                guild_id=guild.id,
                data={
                    'type': 'guild_created',
                    'guild': guild.to_dict()
                }
            ))

            return {
                "success": True,
                "message": f"Guild {name} created successfully",
                "guild": guild.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to create guild: {str(e)}"
            }

    def update_settings(self, guild_id: int, settings: Dict, user: User) -> Dict:
        """Update guild settings"""
        try:
            guild = Guild.query.get(guild_id)
            if not guild:
                return {"success": False, "message": "Guild not found"}

            if not user.can_manage_guild_settings(guild):
                return {"success": False, "message": "Insufficient permissions"}

            # Update settings
            for key, value in settings.items():
                if hasattr(guild, key):
                    setattr(guild, key, value)

            db.session.commit()

            # Emit settings update event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=guild.id,
                data={
                    'type': 'settings_updated',
                    'settings': settings
                }
            ))

            return {
                "success": True,
                "message": "Guild settings updated successfully"
            }

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}

    def manage_member(self, guild_id: int, target_id: int, action: str, user: User) -> Dict:
        """Manage guild members (promote, demote, kick)"""
        try:
            guild = Guild.query.get(guild_id)
            if not guild:
                return {"success": False, "message": "Guild not found"}

            target = User.query.get(target_id)
            if not target:
                return {"success": False, "message": "Target user not found"}

            if action == 'promote':
                if not user.can_promote_members(guild):
                    return {"success": False, "message": "Insufficient permissions"}
                
                result = self._promote_member(guild, target)
                
            elif action == 'demote':
                if not user.can_demote_members(guild):
                    return {"success": False, "message": "Insufficient permissions"}
                
                result = self._demote_member(guild, target)
                
            elif action == 'kick':
                if not user.can_kick_members(guild):
                    return {"success": False, "message": "Insufficient permissions"}
                
                result = self._kick_member(guild, target)
                
            else:
                return {"success": False, "message": "Invalid action"}

            if result["success"]:
                # Emit member update event
                self.event_system.emit_event(GameEvent(
                    type=EventType.GUILD_UPDATE,
                    guild_id=guild.id,
                    user_id=target.id,
                    data={
                        'type': f'member_{action}ed',
                        'member': target.to_dict()
                    }
                ))

            return result

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": str(e)}

    def process_quest_rewards(self, guild: Guild, quest: GuildQuest, rewards: Dict) -> None:
        """Process guild quest rewards"""
        try:
            # Add rewards to guild treasury
            if 'crystals' in rewards:
                guild.crystal_balance += rewards['crystals']
            if 'exons' in rewards:
                guild.exon_balance += rewards['exons']

            # Record transaction
            transaction = GuildTransaction(
                guild_id=guild.id,
                transaction_type='quest_reward',
                crystal_amount=rewards.get('crystals', 0),
                exon_amount=rewards.get('exons', 0),
                description=f"Rewards from quest: {quest.title}"
            )
            db.session.add(transaction)
            
            db.session.commit()

            # Emit treasury update event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=guild.id,
                data={
                    'type': 'treasury_updated',
                    'crystal_balance': str(guild.crystal_balance),
                    'exon_balance': str(guild.exon_balance),
                    'transaction': transaction.to_dict()
                }
            ))

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to process quest rewards: {str(e)}")

    def _promote_member(self, guild: Guild, member: User) -> Dict:
        """Internal method to promote a guild member"""
        current_rank = member.guild_rank
        
        rank_order = ['recruit', 'member', 'veteran', 'officer']
        current_idx = rank_order.index(current_rank)
        
        if current_idx >= len(rank_order) - 1:
            return {
                "success": False,
                "message": "Member already at highest rank"
            }
            
        new_rank = rank_order[current_idx + 1]
        member.guild_rank = new_rank
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Member promoted to {new_rank}"
        }

    def _demote_member(self, guild: Guild, member: User) -> Dict:
        """Internal method to demote a guild member"""
        current_rank = member.guild_rank
        
        rank_order = ['recruit', 'member', 'veteran', 'officer']
        current_idx = rank_order.index(current_rank)
        
        if current_idx <= 0:
            return {
                "success": False,
                "message": "Member already at lowest rank"
            }
            
        new_rank = rank_order[current_idx - 1]
        member.guild_rank = new_rank
        db.session.commit()
        
        return {
            "success": True,
            "message": f"Member demoted to {new_rank}"
        }

    def _kick_member(self, guild: Guild, member: User) -> Dict:
        """Internal method to kick a guild member"""
        if member.id == guild.leader_id:
            return {
                "success": False,
                "message": "Cannot kick guild leader"
            }
            
        member.guild_id = None
        member.guild_rank = None
        db.session.commit()
        
        return {
            "success": True,
            "message": "Member kicked from guild"
        }
