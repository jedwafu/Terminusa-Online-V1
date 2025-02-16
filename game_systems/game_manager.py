from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class GameManager:
    def __init__(self):
        self.logger = logger
        self.logger.info("Initializing Game Manager")
        self.last_update = datetime.utcnow()
        self.active_gates = {}
        self.active_trades = {}
        self.active_sessions = {}

    def update_game_state(self):
        """Update the game state periodically"""
        try:
            current_time = datetime.utcnow()
            time_diff = (current_time - self.last_update).total_seconds()
            
            # Update active gates
            self._update_gates(time_diff)
            
            # Update marketplace
            self._update_marketplace(time_diff)
            
            # Update active sessions
            self._update_sessions(time_diff)
            
            self.last_update = current_time
            
        except Exception as e:
            self.logger.error(f"Error updating game state: {str(e)}", exc_info=True)

    def _update_gates(self, time_diff: float):
        """Update active gates"""
        try:
            # Remove expired gates
            expired_gates = []
            for gate_id, gate_data in self.active_gates.items():
                if gate_data['expires_at'] < datetime.utcnow():
                    expired_gates.append(gate_id)
            
            for gate_id in expired_gates:
                del self.active_gates[gate_id]
                
            self.logger.debug(f"Removed {len(expired_gates)} expired gates")
            
        except Exception as e:
            self.logger.error(f"Error updating gates: {str(e)}", exc_info=True)

    def _update_marketplace(self, time_diff: float):
        """Update marketplace state"""
        try:
            # Remove expired trades
            expired_trades = []
            for trade_id, trade_data in self.active_trades.items():
                if trade_data['expires_at'] < datetime.utcnow():
                    expired_trades.append(trade_id)
            
            for trade_id in expired_trades:
                del self.active_trades[trade_id]
                
            self.logger.debug(f"Removed {len(expired_trades)} expired trades")
            
        except Exception as e:
            self.logger.error(f"Error updating marketplace: {str(e)}", exc_info=True)

    def _update_sessions(self, time_diff: float):
        """Update active game sessions"""
        try:
            # Remove inactive sessions
            inactive_sessions = []
            for session_id, session_data in self.active_sessions.items():
                if (datetime.utcnow() - session_data['last_activity']).total_seconds() > 3600:  # 1 hour timeout
                    inactive_sessions.append(session_id)
            
            for session_id in inactive_sessions:
                del self.active_sessions[session_id]
                
            self.logger.debug(f"Removed {len(inactive_sessions)} inactive sessions")
            
        except Exception as e:
            self.logger.error(f"Error updating sessions: {str(e)}", exc_info=True)

    def process_command(self, command: str, user_id: int, params: Dict) -> Dict:
        """Process a game command from a user"""
        try:
            self.logger.debug(f"Processing command '{command}' for user {user_id} with params: {params}")
            return {'status': 'success', 'message': 'Command processed'}
        except Exception as e:
            self.logger.error(f"Error processing command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def process_gate_entry(self, user, gate, party_members: Optional[List] = None) -> Dict:
        """Process a gate entry request"""
        try:
            self.logger.info(f"Processing gate entry for user {user.id}")
            
            # Add to active gates
            gate_id = f"gate_{len(self.active_gates) + 1}"
            self.active_gates[gate_id] = {
                'gate': gate,
                'users': [user] + (party_members or []),
                'started_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(hours=1)
            }
            
            return {'status': 'success', 'message': 'Gate entry processed', 'gate_id': gate_id}
        except Exception as e:
            self.logger.error(f"Error processing gate entry: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def process_marketplace_action(self, action: str, user, **kwargs) -> Dict:
        """Process marketplace actions"""
        try:
            self.logger.info(f"Processing marketplace action '{action}' for user {user.id}")
            
            if action == 'create_listing':
                trade_id = f"trade_{len(self.active_trades) + 1}"
                self.active_trades[trade_id] = {
                    'seller': user,
                    'item': kwargs.get('item'),
                    'price': kwargs.get('price'),
                    'created_at': datetime.utcnow(),
                    'expires_at': datetime.utcnow() + timedelta(days=kwargs.get('duration', 7))
                }
                return {'status': 'success', 'message': 'Listing created', 'trade_id': trade_id}
                
            elif action == 'cancel_listing':
                trade_id = kwargs.get('trade_id')
                if trade_id in self.active_trades:
                    del self.active_trades[trade_id]
                    return {'status': 'success', 'message': 'Listing cancelled'}
                    
            return {'status': 'error', 'message': 'Invalid action'}
            
        except Exception as e:
            self.logger.error(f"Error processing marketplace action: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def process_token_swap(self, user, from_currency: str, to_currency: str, amount: float) -> Dict:
        """Process token swap requests"""
        try:
            self.logger.info(f"Processing token swap for user {user.id}")
            return {'status': 'success', 'message': 'Token swap processed'}
        except Exception as e:
            self.logger.error(f"Error processing token swap: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def process_gacha_pull(self, user, gacha_type: str, pulls: int = 1) -> Dict:
        """Process gacha pull requests"""
        try:
            self.logger.info(f"Processing gacha pull for user {user.id}")
            return {'status': 'success', 'message': 'Gacha pull processed'}
        except Exception as e:
            self.logger.error(f"Error processing gacha pull: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def process_achievement_update(self, user) -> List[Dict]:
        """Check and process achievement updates"""
        try:
            self.logger.info(f"Processing achievement update for user {user.id}")
            return []
        except Exception as e:
            self.logger.error(f"Error processing achievement update: {str(e)}", exc_info=True)
            return []
