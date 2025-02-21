from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio
import logging

from models import db, Guild, GuildWar, WarTerritory, WarEvent, User
from models.guild_war import TerritoryStatus
from game_systems.territory_control import TerritoryControl
from game_systems.territory_websocket import TerritoryWebSocket
from game_systems.event_system import EventSystem, EventType, GameEvent
from game_systems.achievement_triggers import AchievementTriggers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TerritoryManager:
    def __init__(self, websocket):
        self.territory_control = TerritoryControl(websocket)
        self.territory_websocket = TerritoryWebSocket(websocket)
        self.event_system = EventSystem(websocket)
        self.achievement_triggers = AchievementTriggers(websocket)

        # Start territory update loop
        asyncio.create_task(self.territory_websocket.start_territory_updates())

    async def process_territory_action(self, action: str, territory_id: int, 
                                     user: User, data: Dict) -> Dict:
        """Process territory action"""
        try:
            territory = WarTerritory.query.get(territory_id)
            if not territory:
                return {
                    "success": False,
                    "message": "Territory not found"
                }

            if action == 'attack':
                return await self._handle_attack(territory, user, data)
            elif action == 'reinforce':
                return await self._handle_reinforce(territory, user, data)
            else:
                return {
                    "success": False,
                    "message": "Invalid action"
                }

        except Exception as e:
            logger.error(f"Territory action error: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process territory action"
            }

    async def _handle_attack(self, territory: WarTerritory, user: User, 
                           data: Dict) -> Dict:
        """Handle territory attack"""
        try:
            # Validate attack
            if not self._can_attack(territory, user):
                return {
                    "success": False,
                    "message": "Cannot attack this territory"
                }

            attacking_force = data.get('attacking_force', 0)
            if attacking_force <= 0:
                return {
                    "success": False,
                    "message": "Invalid attack force"
                }

            # Process attack
            old_status = territory.status
            old_controller = territory.controller_id

            attack_result = self.territory_control.process_attack(
                territory=territory,
                attacker=user,
                attacking_force=attacking_force
            )

            if attack_result['success']:
                # Update territory
                territory.status = attack_result['new_status']
                territory.controller_id = user.guild_id if attack_result['captured'] else territory.controller_id
                territory.defense_data = attack_result['defense_data']
                
                # Create war event
                event = WarEvent(
                    war_id=territory.war_id,
                    type='territory_attack',
                    initiator_id=user.id,
                    target_id=territory.id,
                    points=attack_result['points'],
                    details={
                        'attacking_force': attacking_force,
                        'success': attack_result['captured'],
                        'old_controller': old_controller
                    }
                )
                db.session.add(event)
                
                # Update war scores if territory was captured
                if attack_result['captured']:
                    war = territory.war
                    war.scores[str(user.guild_id)] = war.scores.get(str(user.guild_id), 0) + attack_result['points']
                
                db.session.commit()

                # Send WebSocket updates
                await self._send_territory_updates(
                    territory=territory,
                    old_status=old_status,
                    action_type='attack',
                    user=user,
                    details=attack_result
                )

                # Trigger achievements if territory was captured
                if attack_result['captured']:
                    self.achievement_triggers.handle_territory_capture(
                        territory=territory,
                        user=user
                    )

            return attack_result

        except Exception as e:
            db.session.rollback()
            logger.error(f"Attack handling error: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process attack"
            }

    async def _handle_reinforce(self, territory: WarTerritory, user: User, 
                              data: Dict) -> Dict:
        """Handle territory reinforcement"""
        try:
            # Validate reinforcement
            if not self._can_reinforce(territory, user):
                return {
                    "success": False,
                    "message": "Cannot reinforce this territory"
                }

            reinforcement_amount = data.get('reinforcement_amount', 0)
            if reinforcement_amount <= 0:
                return {
                    "success": False,
                    "message": "Invalid reinforcement amount"
                }

            # Process reinforcement
            old_defense = territory.defense_data.get('reinforcements', 0)
            
            reinforce_result = self.territory_control.process_reinforcement(
                territory=territory,
                reinforcer=user,
                amount=reinforcement_amount
            )

            if reinforce_result['success']:
                # Update territory
                territory.defense_data = reinforce_result['defense_data']
                
                # Create war event
                event = WarEvent(
                    war_id=territory.war_id,
                    type='territory_reinforce',
                    initiator_id=user.id,
                    target_id=territory.id,
                    points=0,
                    details={
                        'reinforcement_amount': reinforcement_amount,
                        'old_defense': old_defense
                    }
                )
                db.session.add(event)
                db.session.commit()

                # Send WebSocket updates
                await self._send_territory_updates(
                    territory=territory,
                    action_type='reinforce',
                    user=user,
                    details=reinforce_result
                )

            return reinforce_result

        except Exception as e:
            db.session.rollback()
            logger.error(f"Reinforce handling error: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process reinforcement"
            }

    async def _send_territory_updates(self, territory: WarTerritory, 
                                    action_type: str, user: User, 
                                    details: Dict, old_status: str = None) -> None:
        """Send territory updates via WebSocket"""
        try:
            # Notify territory status change if applicable
            if old_status and old_status != territory.status:
                self.territory_websocket.notify_territory_status_change(
                    territory=territory,
                    old_status=old_status
                )

            # Notify territory action
            if action_type == 'attack':
                if details.get('captured'):
                    self.territory_websocket.notify_territory_capture(
                        territory=territory,
                        capturer_id=user.id
                    )
            elif action_type == 'reinforce':
                self.territory_websocket.notify_territory_reinforced(
                    territory=territory,
                    reinforcer_id=user.id,
                    amount=details.get('reinforcement_amount', 0)
                )

            # Update territory state for all subscribers
            self.territory_websocket.send_territory_state(territory.id)

        except Exception as e:
            logger.error(f"Failed to send territory updates: {str(e)}")

    def _can_attack(self, territory: WarTerritory, user: User) -> bool:
        """Check if user can attack territory"""
        # Can't attack own territory
        if territory.controller_id == user.guild_id:
            return False

        # Check if user is in war
        if user.guild_id not in [
            territory.war.challenger_id,
            territory.war.target_id
        ]:
            return False

        # Check war status
        if territory.war.status != 'active':
            return False

        # Check attack cooldown
        last_attack = territory.defense_data.get('last_attack')
        if last_attack:
            cooldown = datetime.fromisoformat(last_attack) + timedelta(minutes=5)
            if datetime.utcnow() < cooldown:
                return False

        return True

    def _can_reinforce(self, territory: WarTerritory, user: User) -> bool:
        """Check if user can reinforce territory"""
        # Can only reinforce own territory
        if territory.controller_id != user.guild_id:
            return False

        # Check if user is in war
        if user.guild_id not in [
            territory.war.challenger_id,
            territory.war.target_id
        ]:
            return False

        # Check war status
        if territory.war.status != 'active':
            return False

        return True

    async def start(self):
        """Start territory manager"""
        logger.info("Starting territory manager")
        await self.territory_websocket.start_territory_updates()

    async def stop(self):
        """Stop territory manager"""
        logger.info("Stopping territory manager")
        # Add cleanup code if needed
