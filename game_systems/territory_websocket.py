from typing import Dict, List, Optional
from datetime import datetime
import json
import asyncio

from models import db, Guild, GuildWar, WarTerritory, WarEvent
from models.guild_war import TerritoryStatus
from game_systems.event_system import EventSystem, EventType, GameEvent

class TerritoryWebSocket:
    def __init__(self, websocket):
        self.websocket = websocket
        self.event_system = EventSystem(websocket)
        
        # Track active territory subscriptions
        self.territory_subscriptions = {}  # {territory_id: [user_ids]}
        self.user_subscriptions = {}       # {user_id: [territory_ids]}

        # Initialize event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Set up WebSocket event handlers"""
        @self.websocket.on('territory_subscribe')
        def handle_subscribe(data):
            user_id = data.get('user_id')
            territory_id = data.get('territory_id')
            if user_id and territory_id:
                self.subscribe_to_territory(user_id, territory_id)

        @self.websocket.on('territory_unsubscribe')
        def handle_unsubscribe(data):
            user_id = data.get('user_id')
            territory_id = data.get('territory_id')
            if user_id and territory_id:
                self.unsubscribe_from_territory(user_id, territory_id)

        @self.websocket.on('disconnect')
        def handle_disconnect():
            user_id = self.websocket.user_id
            if user_id:
                self.cleanup_user_subscriptions(user_id)

    def subscribe_to_territory(self, user_id: int, territory_id: int) -> None:
        """Subscribe user to territory updates"""
        # Add to territory subscriptions
        if territory_id not in self.territory_subscriptions:
            self.territory_subscriptions[territory_id] = set()
        self.territory_subscriptions[territory_id].add(user_id)

        # Add to user subscriptions
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(territory_id)

        # Send initial territory state
        self.send_territory_state(territory_id, user_id)

    def unsubscribe_from_territory(self, user_id: int, territory_id: int) -> None:
        """Unsubscribe user from territory updates"""
        # Remove from territory subscriptions
        if territory_id in self.territory_subscriptions:
            self.territory_subscriptions[territory_id].discard(user_id)
            if not self.territory_subscriptions[territory_id]:
                del self.territory_subscriptions[territory_id]

        # Remove from user subscriptions
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(territory_id)
            if not self.user_subscriptions[user_id]:
                del self.user_subscriptions[user_id]

    def cleanup_user_subscriptions(self, user_id: int) -> None:
        """Clean up all subscriptions for a user"""
        if user_id in self.user_subscriptions:
            territory_ids = list(self.user_subscriptions[user_id])
            for territory_id in territory_ids:
                self.unsubscribe_from_territory(user_id, territory_id)

    def send_territory_state(self, territory_id: int, user_id: Optional[int] = None) -> None:
        """Send current territory state to subscribers"""
        try:
            territory = WarTerritory.query.get(territory_id)
            if not territory:
                return

            territory_data = self._prepare_territory_data(territory)
            
            if user_id:
                # Send to specific user
                self.websocket.emit('territory_update', territory_data, room=str(user_id))
            else:
                # Send to all subscribers
                subscribers = self.territory_subscriptions.get(territory_id, set())
                for subscriber_id in subscribers:
                    self.websocket.emit('territory_update', territory_data, room=str(subscriber_id))

        except Exception as e:
            print(f"Failed to send territory state: {str(e)}")

    def broadcast_territory_event(self, territory: WarTerritory, event_type: str, 
                                event_data: Dict) -> None:
        """Broadcast territory event to subscribers"""
        try:
            event_message = {
                'type': event_type,
                'territory': self._prepare_territory_data(territory),
                'event': event_data,
                'timestamp': datetime.utcnow().isoformat()
            }

            subscribers = self.territory_subscriptions.get(territory.id, set())
            for user_id in subscribers:
                self.websocket.emit('territory_event', event_message, room=str(user_id))

        except Exception as e:
            print(f"Failed to broadcast territory event: {str(e)}")

    def notify_territory_status_change(self, territory: WarTerritory, 
                                     old_status: str) -> None:
        """Notify subscribers of territory status change"""
        try:
            status_data = {
                'type': 'status_change',
                'territory_id': territory.id,
                'old_status': old_status,
                'new_status': territory.status,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Emit status change event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=territory.controller_id,
                data={
                    'type': 'territory_status_change',
                    'territory': self._prepare_territory_data(territory),
                    'old_status': old_status,
                    'new_status': territory.status
                }
            ))

            # Notify territory subscribers
            self.broadcast_territory_event(
                territory=territory,
                event_type='status_change',
                event_data=status_data
            )

        except Exception as e:
            print(f"Failed to notify territory status change: {str(e)}")

    def notify_territory_capture(self, territory: WarTerritory, 
                               capturer_id: int) -> None:
        """Notify subscribers of territory capture"""
        try:
            capture_data = {
                'type': 'capture',
                'territory_id': territory.id,
                'capturer_id': capturer_id,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Emit capture event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=territory.controller_id,
                data={
                    'type': 'territory_captured',
                    'territory': self._prepare_territory_data(territory),
                    'capturer_id': capturer_id
                }
            ))

            # Notify territory subscribers
            self.broadcast_territory_event(
                territory=territory,
                event_type='capture',
                event_data=capture_data
            )

        except Exception as e:
            print(f"Failed to notify territory capture: {str(e)}")

    def notify_territory_reinforced(self, territory: WarTerritory, 
                                  reinforcer_id: int, amount: int) -> None:
        """Notify subscribers of territory reinforcement"""
        try:
            reinforce_data = {
                'type': 'reinforce',
                'territory_id': territory.id,
                'reinforcer_id': reinforcer_id,
                'amount': amount,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Emit reinforcement event
            self.event_system.emit_event(GameEvent(
                type=EventType.GUILD_UPDATE,
                guild_id=territory.controller_id,
                data={
                    'type': 'territory_reinforced',
                    'territory': self._prepare_territory_data(territory),
                    'reinforcer_id': reinforcer_id,
                    'amount': amount
                }
            ))

            # Notify territory subscribers
            self.broadcast_territory_event(
                territory=territory,
                event_type='reinforce',
                event_data=reinforce_data
            )

        except Exception as e:
            print(f"Failed to notify territory reinforcement: {str(e)}")

    def _prepare_territory_data(self, territory: WarTerritory) -> Dict:
        """Prepare territory data for WebSocket transmission"""
        return {
            'id': territory.id,
            'name': territory.name,
            'type': territory.type,
            'status': territory.status,
            'controller_id': territory.controller_id,
            'controller_name': territory.controller.name if territory.controller else None,
            'position_x': territory.position_x,
            'position_y': territory.position_y,
            'bonuses': territory.bonuses,
            'defense_data': territory.defense_data,
            'last_update': datetime.utcnow().isoformat()
        }

    async def start_territory_updates(self):
        """Start periodic territory updates"""
        while True:
            try:
                # Update all active territories
                active_territories = WarTerritory.query.filter(
                    WarTerritory.war_id.in_(
                        db.session.query(GuildWar.id).filter_by(
                            status='active'
                        )
                    )
                ).all()

                for territory in active_territories:
                    if territory.id in self.territory_subscriptions:
                        self.send_territory_state(territory.id)

                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                print(f"Territory update error: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
