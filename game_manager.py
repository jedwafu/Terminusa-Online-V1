"""
Game Manager for Terminusa Online
"""
from typing import Dict, Optional
import logging
from models import db, User
from game_systems.combat_manager import CombatManager
from game_systems.gate_system import GateSystem
from game_systems.currency_system import CurrencySystem
from game_systems.job_system import JobSystem
from game_systems.guild_system import GuildSystem
from game_systems.party_system import PartySystem
from game_systems.equipment_system import EquipmentSystem
from game_systems.achievement_system import AchievementSystem
from game_systems.gambling_system import GamblingSystem
from game_systems.gacha_system import GachaSystem
from game_systems.hunter_shop import HunterShop
from game_systems.ai_agent import AIAgent

logger = logging.getLogger(__name__)

class GameManager:
    """Coordinates game systems and manages overall game state"""
    
    def __init__(self):
        # Initialize all game systems
        self.combat_manager = CombatManager()
        self.gate_system = GateSystem()
        self.currency_system = CurrencySystem()
        self.job_system = JobSystem()
        self.guild_system = GuildSystem()
        self.party_system = PartySystem()
        self.equipment_system = EquipmentSystem()
        self.achievement_system = AchievementSystem()
        self.gambling_system = GamblingSystem()
        self.gacha_system = GachaSystem()
        self.hunter_shop = HunterShop()
        self.ai_agent = AIAgent()

    def process_user_action(self, user: User, action: str, params: Dict) -> Dict:
        """Process user action and coordinate between systems"""
        try:
            # Update achievements first to track any potential progress
            self.achievement_system.check_achievements(user)
            
            # Process action based on type
            if action.startswith('combat_'):
                return self._handle_combat_action(user, action, params)
            elif action.startswith('gate_'):
                return self._handle_gate_action(user, action, params)
            elif action.startswith('currency_'):
                return self._handle_currency_action(user, action, params)
            elif action.startswith('job_'):
                return self._handle_job_action(user, action, params)
            elif action.startswith('guild_'):
                return self._handle_guild_action(user, action, params)
            elif action.startswith('party_'):
                return self._handle_party_action(user, action, params)
            elif action.startswith('equipment_'):
                return self._handle_equipment_action(user, action, params)
            elif action.startswith('gamble_'):
                return self._handle_gambling_action(user, action, params)
            elif action.startswith('gacha_'):
                return self._handle_gacha_action(user, action, params)
            elif action.startswith('shop_'):
                return self._handle_shop_action(user, action, params)
            else:
                return {
                    "success": False,
                    "message": "Invalid action"
                }

        except Exception as e:
            logger.error(f"Failed to process action {action}: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process action"
            }

    def _handle_combat_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle combat-related actions"""
        try:
            if action == 'combat_attack':
                return self.combat_manager.process_combat_round(params['battle_id'])
            elif action == 'combat_use_skill':
                return self.combat_manager.use_skill(
                    params['battle_id'],
                    params['skill_id']
                )
            elif action == 'combat_use_item':
                return self.combat_manager.use_item(
                    params['battle_id'],
                    params['item_id']
                )
            return {
                "success": False,
                "message": "Invalid combat action"
            }

        except Exception as e:
            logger.error(f"Failed to handle combat action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle combat action"
            }

    def _handle_gate_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle gate-related actions"""
        try:
            if action == 'gate_enter':
                return self.gate_system.enter_gate(
                    user,
                    params['gate_id'],
                    params.get('party')
                )
            elif action == 'gate_leave':
                return self.gate_system.leave_gate(user, params['gate_id'])
            return {
                "success": False,
                "message": "Invalid gate action"
            }

        except Exception as e:
            logger.error(f"Failed to handle gate action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle gate action"
            }

    def _handle_currency_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle currency-related actions"""
        try:
            if action == 'currency_transfer':
                return self.currency_system.transfer_currency(
                    user,
                    params['recipient_id'],
                    params['currency'],
                    params['amount']
                )
            elif action == 'currency_swap':
                return self.currency_system.swap_currency(
                    user,
                    params['from_currency'],
                    params['to_currency'],
                    params['amount']
                )
            return {
                "success": False,
                "message": "Invalid currency action"
            }

        except Exception as e:
            logger.error(f"Failed to handle currency action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle currency action"
            }

    def _handle_job_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle job-related actions"""
        try:
            if action == 'job_change':
                return self.job_system.change_job(user, params['new_job'])
            elif action == 'job_reset':
                return self.job_system.reset_job(user)
            return {
                "success": False,
                "message": "Invalid job action"
            }

        except Exception as e:
            logger.error(f"Failed to handle job action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle job action"
            }

    def _handle_guild_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle guild-related actions"""
        try:
            if action == 'guild_create':
                return self.guild_system.create_guild(
                    user,
                    params['name'],
                    params['description']
                )
            elif action == 'guild_join':
                return self.guild_system.join_guild(user, params['guild_id'])
            elif action == 'guild_leave':
                return self.guild_system.leave_guild(user)
            return {
                "success": False,
                "message": "Invalid guild action"
            }

        except Exception as e:
            logger.error(f"Failed to handle guild action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle guild action"
            }

    def _handle_party_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle party-related actions"""
        try:
            if action == 'party_create':
                return self.party_system.create_party(user, params['name'])
            elif action == 'party_join':
                return self.party_system.join_party(user, params['party_id'])
            elif action == 'party_leave':
                return self.party_system.leave_party(user)
            elif action == 'party_ready':
                return self.party_system.set_ready_status(
                    user,
                    params['is_ready']
                )
            return {
                "success": False,
                "message": "Invalid party action"
            }

        except Exception as e:
            logger.error(f"Failed to handle party action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle party action"
            }

    def _handle_equipment_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle equipment-related actions"""
        try:
            if action == 'equipment_equip':
                return self.equipment_system.equip_item(
                    user,
                    params['equipment_id']
                )
            elif action == 'equipment_unequip':
                return self.equipment_system.unequip_item(
                    user,
                    params['equipment_id']
                )
            elif action == 'equipment_upgrade':
                return self.equipment_system.upgrade_equipment(
                    user,
                    params['equipment_id']
                )
            elif action == 'equipment_repair':
                return self.equipment_system.repair_equipment(
                    user,
                    params['equipment_id']
                )
            return {
                "success": False,
                "message": "Invalid equipment action"
            }

        except Exception as e:
            logger.error(f"Failed to handle equipment action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle equipment action"
            }

    def _handle_gambling_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle gambling-related actions"""
        try:
            if action == 'gamble_flip_coin':
                return self.gambling_system.flip_coin(user, params['bet_amount'])
            return {
                "success": False,
                "message": "Invalid gambling action"
            }

        except Exception as e:
            logger.error(f"Failed to handle gambling action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle gambling action"
            }

    def _handle_gacha_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle gacha-related actions"""
        try:
            if action == 'gacha_summon_mount':
                return self.gacha_system.summon_mount(user)
            elif action == 'gacha_summon_pet':
                return self.gacha_system.summon_pet(user)
            return {
                "success": False,
                "message": "Invalid gacha action"
            }

        except Exception as e:
            logger.error(f"Failed to handle gacha action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle gacha action"
            }

    def _handle_shop_action(self, user: User, action: str, params: Dict) -> Dict:
        """Handle shop-related actions"""
        try:
            if action == 'shop_purchase':
                return self.hunter_shop.purchase_item(
                    user,
                    params['item_id'],
                    params.get('quantity', 1)
                )
            return {
                "success": False,
                "message": "Invalid shop action"
            }

        except Exception as e:
            logger.error(f"Failed to handle shop action: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle shop action"
            }

    def get_user_state(self, user: User) -> Dict:
        """Get comprehensive user state"""
        try:
            # Get AI insights
            profile = self.ai_agent.analyze_player(user)

            return {
                "success": True,
                "state": {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "level": user.level,
                        "experience": user.experience,
                        "job_class": user.job_class,
                        "job_level": user.job_level,
                        "crystals": user.crystals,
                        "exons_balance": user.exons_balance
                    },
                    "stats": {
                        "hp": user.hp,
                        "max_hp": user.max_hp,
                        "mp": user.mp,
                        "max_mp": user.max_mp,
                        "attack": user.attack,
                        "defense": user.defense,
                        "magic_attack": user.magic_attack,
                        "magic_defense": user.magic_defense
                    },
                    "equipment": self.equipment_system._get_equipment_stats(user),
                    "party": self._get_party_state(user),
                    "guild": self._get_guild_state(user),
                    "achievements": self.achievement_system.get_achievements(user),
                    "ai_insights": profile if profile else {}
                }
            }

        except Exception as e:
            logger.error(f"Failed to get user state: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get user state"
            }

    def _get_party_state(self, user: User) -> Optional[Dict]:
        """Get user's party state"""
        try:
            party = self.party_system._get_user_party(user)
            if party:
                return self.party_system.get_party_info(party.id)["party"]
            return None
        except Exception:
            return None

    def _get_guild_state(self, user: User) -> Optional[Dict]:
        """Get user's guild state"""
        try:
            if user.guild_id:
                return self.guild_system.get_guild_info(user.guild_id)["guild"]
            return None
        except Exception:
            return None
