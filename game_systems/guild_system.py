"""
Guild System for Terminusa Online
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import random
import logging
from models import db, User, Guild, GuildMember, GuildQuest, Transaction
from game_systems.ai_agent import AIAgent
from game_config import (
    GUILD_CONFIG,
    CRYSTAL_TAX_RATE,
    GUILD_CRYSTAL_TAX_RATE,
    EXON_TAX_RATE,
    GUILD_EXON_TAX_RATE
)

logger = logging.getLogger(__name__)

class GuildSystem:
    """Handles guild management and guild-related features"""
    
    def __init__(self):
        self.ai_agent = AIAgent()
        self._rank_permissions = {
            'Leader': ['manage_members', 'manage_quests', 'manage_bank', 'manage_ranks'],
            'Officer': ['manage_members', 'manage_quests'],
            'Veteran': ['access_bank', 'accept_quests'],
            'Member': ['accept_quests'],
            'Recruit': ['view_quests']
        }

    def create_guild(self, leader: User, name: str, description: str) -> Dict:
        """Create a new guild"""
        try:
            # Check if user is already in a guild
            if leader.guild_id:
                return {
                    "success": False,
                    "message": "Already in a guild"
                }

            # Check if name is taken
            if Guild.query.filter_by(name=name).first():
                return {
                    "success": False,
                    "message": "Guild name already taken"
                }

            # Check creation costs
            if (leader.crystals < GUILD_CONFIG['creation_cost']['crystals'] or
                leader.exons_balance < GUILD_CONFIG['creation_cost']['exons']):
                return {
                    "success": False,
                    "message": "Insufficient funds for guild creation"
                }

            # Create guild
            guild = Guild(
                name=name,
                description=description,
                leader_id=leader.id,
                created_at=datetime.utcnow(),
                crystal_balance=0,
                exon_balance=0
            )
            db.session.add(guild)
            db.session.flush()  # Get guild ID

            # Add leader as member
            member = GuildMember(
                guild_id=guild.id,
                user_id=leader.id,
                rank='Leader',
                joined_at=datetime.utcnow()
            )
            db.session.add(member)

            # Deduct creation costs
            leader.crystals -= GUILD_CONFIG['creation_cost']['crystals']
            leader.exons_balance -= GUILD_CONFIG['creation_cost']['exons']

            # Record transaction
            transaction = Transaction(
                user_id=leader.id,
                type='guild_creation',
                currency='mixed',
                amount=GUILD_CONFIG['creation_cost']['crystals'],
                metadata={
                    'crystals': GUILD_CONFIG['creation_cost']['crystals'],
                    'exons': GUILD_CONFIG['creation_cost']['exons'],
                    'guild_id': guild.id
                }
            )
            db.session.add(transaction)

            db.session.commit()

            return {
                "success": True,
                "message": "Guild created successfully",
                "guild_id": guild.id
            }

        except Exception as e:
            logger.error(f"Failed to create guild: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to create guild"
            }

    def join_guild(self, user: User, guild_id: int) -> Dict:
        """Join a guild"""
        try:
            # Check if user is already in a guild
            if user.guild_id:
                return {
                    "success": False,
                    "message": "Already in a guild"
                }

            guild = Guild.query.get(guild_id)
            if not guild:
                return {
                    "success": False,
                    "message": "Guild not found"
                }

            # Check member limit
            current_members = GuildMember.query.filter_by(guild_id=guild_id).count()
            if current_members >= GUILD_CONFIG['max_members']:
                return {
                    "success": False,
                    "message": "Guild is full"
                }

            # Add member
            member = GuildMember(
                guild_id=guild_id,
                user_id=user.id,
                rank='Recruit',
                joined_at=datetime.utcnow()
            )
            db.session.add(member)
            db.session.commit()

            return {
                "success": True,
                "message": "Successfully joined guild"
            }

        except Exception as e:
            logger.error(f"Failed to join guild: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to join guild"
            }

    def leave_guild(self, user: User) -> Dict:
        """Leave current guild"""
        try:
            if not user.guild_id:
                return {
                    "success": False,
                    "message": "Not in a guild"
                }

            # Check if user is guild leader
            guild = Guild.query.get(user.guild_id)
            if guild.leader_id == user.id:
                return {
                    "success": False,
                    "message": "Guild leader must assign new leader before leaving"
                }

            # Remove member
            GuildMember.query.filter_by(
                guild_id=user.guild_id,
                user_id=user.id
            ).delete()

            db.session.commit()

            return {
                "success": True,
                "message": "Successfully left guild"
            }

        except Exception as e:
            logger.error(f"Failed to leave guild: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to leave guild"
            }

    def manage_member(self, actor: User, target_id: int, action: str, new_rank: Optional[str] = None) -> Dict:
        """Manage guild member (promote, demote, kick)"""
        try:
            if not actor.guild_id:
                return {
                    "success": False,
                    "message": "Not in a guild"
                }

            # Check permissions
            actor_member = GuildMember.query.filter_by(
                guild_id=actor.guild_id,
                user_id=actor.id
            ).first()
            
            if not self._has_permission(actor_member.rank, 'manage_members'):
                return {
                    "success": False,
                    "message": "Insufficient permissions"
                }

            # Get target member
            target_member = GuildMember.query.filter_by(
                guild_id=actor.guild_id,
                user_id=target_id
            ).first()
            
            if not target_member:
                return {
                    "success": False,
                    "message": "Target member not found"
                }

            if action == 'kick':
                # Can't kick guild leader
                guild = Guild.query.get(actor.guild_id)
                if target_id == guild.leader_id:
                    return {
                        "success": False,
                        "message": "Cannot kick guild leader"
                    }
                
                db.session.delete(target_member)
                message = "Member kicked successfully"
                
            elif action == 'promote' and new_rank:
                if new_rank not in self._rank_permissions:
                    return {
                        "success": False,
                        "message": "Invalid rank"
                    }
                
                target_member.rank = new_rank
                message = f"Member promoted to {new_rank}"
                
            elif action == 'demote' and new_rank:
                if new_rank not in self._rank_permissions:
                    return {
                        "success": False,
                        "message": "Invalid rank"
                    }
                
                target_member.rank = new_rank
                message = f"Member demoted to {new_rank}"
                
            else:
                return {
                    "success": False,
                    "message": "Invalid action"
                }

            db.session.commit()

            return {
                "success": True,
                "message": message
            }

        except Exception as e:
            logger.error(f"Failed to manage member: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to manage member"
            }

    def generate_guild_quest(self, guild_id: int) -> Dict:
        """Generate AI-driven guild quest"""
        try:
            guild = Guild.query.get(guild_id)
            if not guild:
                return {
                    "success": False,
                    "message": "Guild not found"
                }

            # Get guild members for AI analysis
            members = User.query.join(GuildMember).filter(
                GuildMember.guild_id == guild_id
            ).all()

            # Use AI to generate appropriate quest
            quest_params = self.ai_agent.generate_quest(random.choice(members))
            if not quest_params['success']:
                return quest_params

            # Enhance rewards for guild quest
            rewards = quest_params['quest']['rewards']
            rewards['crystals'] = int(rewards['crystals'] * GUILD_CONFIG['quest_reward_multiplier'])
            rewards['experience'] = int(rewards['experience'] * GUILD_CONFIG['quest_reward_multiplier'])

            quest = GuildQuest(
                guild_id=guild_id,
                title=f"Guild Quest: {quest_params['quest']['title']}",
                description=quest_params['quest']['description'],
                difficulty=quest_params['quest']['difficulty'],
                parameters=quest_params['quest']['parameters'],
                rewards=rewards,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=1)
            )

            db.session.add(quest)
            db.session.commit()

            return {
                "success": True,
                "message": "Guild quest generated",
                "quest": quest.to_dict()
            }

        except Exception as e:
            logger.error(f"Failed to generate guild quest: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to generate guild quest"
            }

    def complete_guild_quest(self, quest_id: int, members: List[User]) -> Dict:
        """Complete guild quest and distribute rewards"""
        try:
            quest = GuildQuest.query.get(quest_id)
            if not quest:
                return {
                    "success": False,
                    "message": "Quest not found"
                }

            if quest.completed_at:
                return {
                    "success": False,
                    "message": "Quest already completed"
                }

            # Calculate rewards
            base_rewards = quest.rewards
            member_share = len(members)
            
            # Calculate tax
            crystal_tax = int(base_rewards['crystals'] * GUILD_CONFIG['quest_tax_rate'])
            net_crystals = base_rewards['crystals'] - crystal_tax
            
            # Distribute rewards
            crystal_share = net_crystals // member_share
            exp_share = base_rewards['experience'] // member_share
            
            for member in members:
                # Add crystals
                member.crystals += crystal_share
                
                # Add experience
                member.experience += exp_share
                
                # Add items if any
                if 'items' in base_rewards:
                    for item in base_rewards['items']:
                        self._add_item_to_inventory(member, item)

            # Mark quest completed
            quest.completed_at = datetime.utcnow()
            quest.completed_by = [member.id for member in members]

            db.session.commit()

            return {
                "success": True,
                "message": "Quest completed successfully",
                "rewards": {
                    "crystals_per_member": crystal_share,
                    "experience_per_member": exp_share,
                    "items": base_rewards.get('items', [])
                }
            }

        except Exception as e:
            logger.error(f"Failed to complete guild quest: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to complete guild quest"
            }

    def manage_guild_bank(self, actor: User, action: str, currency: str, amount: Decimal) -> Dict:
        """Manage guild bank (deposit/withdraw)"""
        try:
            if not actor.guild_id:
                return {
                    "success": False,
                    "message": "Not in a guild"
                }

            # Check permissions
            actor_member = GuildMember.query.filter_by(
                guild_id=actor.guild_id,
                user_id=actor.id
            ).first()
            
            if not self._has_permission(actor_member.rank, 'manage_bank'):
                return {
                    "success": False,
                    "message": "Insufficient permissions"
                }

            guild = Guild.query.get(actor.guild_id)
            
            if action == 'deposit':
                # Check user balance
                if currency == 'crystals':
                    if actor.crystals < amount:
                        return {
                            "success": False,
                            "message": "Insufficient crystals"
                        }
                    actor.crystals -= amount
                    guild.crystal_balance += amount
                else:  # exons
                    if actor.exons_balance < amount:
                        return {
                            "success": False,
                            "message": "Insufficient exons"
                        }
                    actor.exons_balance -= amount
                    guild.exon_balance += amount
                
                message = f"Deposited {amount} {currency} to guild bank"
                
            elif action == 'withdraw':
                # Check guild balance
                if currency == 'crystals':
                    if guild.crystal_balance < amount:
                        return {
                            "success": False,
                            "message": "Insufficient guild crystals"
                        }
                    guild.crystal_balance -= amount
                    actor.crystals += amount
                else:  # exons
                    if guild.exon_balance < amount:
                        return {
                            "success": False,
                            "message": "Insufficient guild exons"
                        }
                    guild.exon_balance -= amount
                    actor.exons_balance += amount
                
                message = f"Withdrew {amount} {currency} from guild bank"
                
            else:
                return {
                    "success": False,
                    "message": "Invalid action"
                }

            # Record transaction
            transaction = Transaction(
                user_id=actor.id,
                type=f'guild_bank_{action}',
                currency=currency,
                amount=amount,
                metadata={'guild_id': guild.id}
            )
            db.session.add(transaction)

            db.session.commit()

            return {
                "success": True,
                "message": message,
                "new_balance": {
                    "crystals": guild.crystal_balance,
                    "exons": guild.exon_balance
                }
            }

        except Exception as e:
            logger.error(f"Failed to manage guild bank: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to manage guild bank"
            }

    def _has_permission(self, rank: str, permission: str) -> bool:
        """Check if rank has permission"""
        return permission in self._rank_permissions.get(rank, [])

    def _add_item_to_inventory(self, user: User, item: Dict) -> None:
        """Add item to user's inventory"""
        try:
            inventory_item = Item(
                user_id=user.id,
                item_id=item['id'],
                quantity=item.get('quantity', 1)
            )
            db.session.add(inventory_item)
        except Exception as e:
            logger.error(f"Failed to add item to inventory: {str(e)}")
            raise
