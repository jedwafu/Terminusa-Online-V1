from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from models import db, User, Guild, Gate, Transaction
from websocket_manager import WebSocketManager

class EventType(Enum):
    GATE_CLEAR = "gate_clear"
    LEVEL_UP = "level_up"
    ACHIEVEMENT = "achievement"
    GUILD_UPDATE = "guild_update"
    MARKET_UPDATE = "market_update"
    CURRENCY_UPDATE = "currency_update"
    INVENTORY_UPDATE = "inventory_update"
    COMBAT_UPDATE = "combat_update"
    QUEST_UPDATE = "quest_update"
    LEADERBOARD_UPDATE = "leaderboard_update"
    ANNOUNCEMENT = "announcement"

@dataclass
class GameEvent:
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()
    user_id: Optional[int] = None
    guild_id: Optional[int] = None
    gate_id: Optional[int] = None

class EventSystem:
    def __init__(self, websocket: WebSocketManager):
        self.websocket = websocket
        self.event_handlers = {
            EventType.GATE_CLEAR: self._handle_gate_clear,
            EventType.LEVEL_UP: self._handle_level_up,
            EventType.ACHIEVEMENT: self._handle_achievement,
            EventType.GUILD_UPDATE: self._handle_guild_update,
            EventType.MARKET_UPDATE: self._handle_market_update,
            EventType.CURRENCY_UPDATE: self._handle_currency_update,
            EventType.INVENTORY_UPDATE: self._handle_inventory_update,
            EventType.COMBAT_UPDATE: self._handle_combat_update,
            EventType.QUEST_UPDATE: self._handle_quest_update,
            EventType.LEADERBOARD_UPDATE: self._handle_leaderboard_update,
            EventType.ANNOUNCEMENT: self._handle_announcement
        }

    def emit_event(self, event: GameEvent):
        """Process and emit a game event"""
        # Handle the event
        handler = self.event_handlers.get(event.type)
        if handler:
            handler(event)

        # Log the event
        self._log_event(event)

    def _handle_gate_clear(self, event: GameEvent):
        """Handle gate clear events"""
        # Update leaderboards
        self._update_leaderboards()
        
        # Notify guild members if in a guild
        if event.guild_id:
            self.websocket.emit_to_guild(
                event.guild_id,
                'gate_clear',
                {
                    'gate_id': event.gate_id,
                    'cleared_by': event.data.get('cleared_by'),
                    'rewards': event.data.get('rewards')
                }
            )

        # Notify party members
        if event.data.get('party_members'):
            for member_id in event.data['party_members']:
                self.websocket.emit_to_user(
                    member_id,
                    'gate_clear',
                    event.data
                )

    def _handle_level_up(self, event: GameEvent):
        """Handle level up events"""
        user_id = event.user_id
        if not user_id:
            return

        # Update user's stats
        self.websocket.emit_to_user(
            user_id,
            'stats_update',
            event.data
        )

        # Notify guild members if in a guild
        if event.guild_id:
            self.websocket.emit_to_guild(
                event.guild_id,
                'member_level_up',
                {
                    'user_id': user_id,
                    'new_level': event.data.get('new_level')
                }
            )

        # Update leaderboards if significant level
        if event.data.get('new_level', 0) % 10 == 0:
            self._update_leaderboards()

    def _handle_achievement(self, event: GameEvent):
        """Handle achievement completion events"""
        user_id = event.user_id
        if not user_id:
            return

        # Notify user
        self.websocket.emit_to_user(
            user_id,
            'achievement_complete',
            event.data
        )

        # Notify guild members if in a guild
        if event.guild_id:
            self.websocket.emit_to_guild(
                event.guild_id,
                'member_achievement',
                {
                    'user_id': user_id,
                    'achievement': event.data.get('achievement')
                }
            )

    def _handle_guild_update(self, event: GameEvent):
        """Handle guild update events"""
        guild_id = event.guild_id
        if not guild_id:
            return

        # Notify all guild members
        self.websocket.emit_to_guild(
            guild_id,
            'guild_update',
            event.data
        )

        # Update leaderboards if significant change
        if event.data.get('significant_change', False):
            self._update_leaderboards()

    def _handle_market_update(self, event: GameEvent):
        """Handle market update events"""
        # Broadcast market updates to all users
        self.websocket.notify_market_update(event.data)

    def _handle_currency_update(self, event: GameEvent):
        """Handle currency update events"""
        user_id = event.user_id
        if not user_id:
            return

        # Notify user of currency changes
        self.websocket.notify_currency_update(user_id, event.data)

    def _handle_inventory_update(self, event: GameEvent):
        """Handle inventory update events"""
        user_id = event.user_id
        if not user_id:
            return

        # Notify user of inventory changes
        self.websocket.notify_inventory_update(user_id, event.data)

    def _handle_combat_update(self, event: GameEvent):
        """Handle combat update events"""
        gate_id = event.gate_id
        if not gate_id:
            return

        # Notify all users in the gate
        self.websocket.notify_combat_update(gate_id, event.data)

    def _handle_quest_update(self, event: GameEvent):
        """Handle quest update events"""
        user_id = event.user_id
        if not user_id:
            return

        # Notify user of quest updates
        self.websocket.emit_to_user(
            user_id,
            'quest_update',
            event.data
        )

        # Notify guild if guild quest
        if event.guild_id and event.data.get('is_guild_quest', False):
            self.websocket.emit_to_guild(
                event.guild_id,
                'guild_quest_update',
                event.data
            )

    def _handle_leaderboard_update(self, event: GameEvent):
        """Handle leaderboard update events"""
        # Broadcast leaderboard updates to all users
        self.websocket.notify_leaderboard_update(event.data)

    def _handle_announcement(self, event: GameEvent):
        """Handle announcement events"""
        # Broadcast announcement to all users
        self.websocket.broadcast_announcement(event.data.get('message', ''))

    def _update_leaderboards(self):
        """Update all leaderboards"""
        # Get updated rankings
        hunter_rankings = self._get_hunter_rankings()
        guild_rankings = self._get_guild_rankings()
        gate_rankings = self._get_gate_rankings()

        # Broadcast updates
        self.websocket.notify_leaderboard_update({
            'hunters': hunter_rankings,
            'guilds': guild_rankings,
            'gates': gate_rankings
        })

    def _get_hunter_rankings(self) -> List[Dict]:
        """Get current hunter rankings"""
        hunters = User.query.order_by(
            User.level.desc(),
            User.gates_cleared.desc()
        ).limit(100).all()
        
        return [hunter.to_ranking_dict() for hunter in hunters]

    def _get_guild_rankings(self) -> List[Dict]:
        """Get current guild rankings"""
        guilds = Guild.query.order_by(
            Guild.level.desc(),
            Guild.total_gates_cleared.desc()
        ).limit(50).all()
        
        return [guild.to_ranking_dict() for guild in guilds]

    def _get_gate_rankings(self) -> List[Dict]:
        """Get current gate rankings"""
        gates = Gate.query.order_by(
            Gate.rank.desc(),
            Gate.total_clears.desc()
        ).all()
        
        return [gate.to_ranking_dict() for gate in gates]

    def _log_event(self, event: GameEvent):
        """Log event to database for analytics"""
        try:
            from models import GameEventLog
            
            log = GameEventLog(
                event_type=event.type.value,
                user_id=event.user_id,
                guild_id=event.guild_id,
                gate_id=event.gate_id,
                data=event.data,
                timestamp=event.timestamp
            )
            
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f"Failed to log event: {e}")
            db.session.rollback()
