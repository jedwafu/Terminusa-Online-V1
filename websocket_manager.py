from typing import Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user

@dataclass
class WebSocketConnection:
    user_id: int
    session_id: str
    connected_at: datetime
    rooms: Set[str]

class WebSocketManager:
    def __init__(self, app: Flask):
        self.socketio = SocketIO(app, cors_allowed_origins="*")
        self.connections: Dict[str, WebSocketConnection] = {}
        
        self.setup_handlers()

    def setup_handlers(self):
        @self.socketio.on('connect')
        def handle_connect():
            if not current_user.is_authenticated:
                return False

            connection = WebSocketConnection(
                user_id=current_user.id,
                session_id=request.sid,
                connected_at=datetime.utcnow(),
                rooms=set()
            )
            self.connections[request.sid] = connection
            
            # Join user's personal room
            join_room(f"user_{current_user.id}")
            connection.rooms.add(f"user_{current_user.id}")
            
            # Join guild room if user is in a guild
            if current_user.guild_id:
                join_room(f"guild_{current_user.guild_id}")
                connection.rooms.add(f"guild_{current_user.guild_id}")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            if request.sid in self.connections:
                connection = self.connections[request.sid]
                # Leave all rooms
                for room in connection.rooms:
                    leave_room(room)
                del self.connections[request.sid]

        @self.socketio.on('join_gate')
        def handle_join_gate(data):
            gate_id = data.get('gate_id')
            if gate_id and request.sid in self.connections:
                room = f"gate_{gate_id}"
                join_room(room)
                self.connections[request.sid].rooms.add(room)

        @self.socketio.on('leave_gate')
        def handle_leave_gate(data):
            gate_id = data.get('gate_id')
            if gate_id and request.sid in self.connections:
                room = f"gate_{gate_id}"
                leave_room(room)
                self.connections[request.sid].rooms.remove(room)

    def emit_to_user(self, user_id: int, event: str, data: dict):
        """Emit event to specific user"""
        self.socketio.emit(event, data, room=f"user_{user_id}")

    def emit_to_guild(self, guild_id: int, event: str, data: dict):
        """Emit event to all guild members"""
        self.socketio.emit(event, data, room=f"guild_{guild_id}")

    def emit_to_gate(self, gate_id: int, event: str, data: dict):
        """Emit event to all users in a gate"""
        self.socketio.emit(event, data, room=f"gate_{gate_id}")

    def broadcast_announcement(self, message: str):
        """Broadcast announcement to all connected users"""
        self.socketio.emit('announcement', {'message': message})

    def notify_currency_update(self, user_id: int, currency_data: dict):
        """Notify user of currency balance changes"""
        self.emit_to_user(user_id, 'currency_update', currency_data)

    def notify_inventory_update(self, user_id: int, inventory_data: dict):
        """Notify user of inventory changes"""
        self.emit_to_user(user_id, 'inventory_update', inventory_data)

    def notify_stats_update(self, user_id: int, stats_data: dict):
        """Notify user of stats changes"""
        self.emit_to_user(user_id, 'stats_update', stats_data)

    def notify_achievement_complete(self, user_id: int, achievement_data: dict):
        """Notify user of achievement completion"""
        self.emit_to_user(user_id, 'achievement_complete', achievement_data)

    def notify_gate_update(self, gate_id: int, update_data: dict):
        """Notify all users in a gate of updates"""
        self.emit_to_gate(gate_id, 'gate_update', update_data)

    def notify_guild_update(self, guild_id: int, update_data: dict):
        """Notify all guild members of updates"""
        self.emit_to_guild(guild_id, 'guild_update', update_data)

    def notify_combat_update(self, gate_id: int, combat_data: dict):
        """Notify users in a gate of combat updates"""
        self.emit_to_gate(gate_id, 'combat_update', combat_data)

    def notify_market_update(self, market_data: dict):
        """Broadcast market updates to all users"""
        self.socketio.emit('market_update', market_data)

    def notify_leaderboard_update(self, leaderboard_data: dict):
        """Broadcast leaderboard updates to all users"""
        self.socketio.emit('leaderboard_update', leaderboard_data)

    def get_active_connections(self, user_id: Optional[int] = None) -> int:
        """Get count of active connections"""
        if user_id:
            return len([c for c in self.connections.values() if c.user_id == user_id])
        return len(self.connections)

    def get_users_in_gate(self, gate_id: int) -> Set[int]:
        """Get set of user IDs currently in a gate"""
        room = f"gate_{gate_id}"
        return {c.user_id for c in self.connections.values() if room in c.rooms}

    def get_online_guild_members(self, guild_id: int) -> Set[int]:
        """Get set of online guild member IDs"""
        room = f"guild_{guild_id}"
        return {c.user_id for c in self.connections.values() if room in c.rooms}

    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the WebSocket server"""
        self.socketio.run(app, host=host, port=port, debug=debug)
