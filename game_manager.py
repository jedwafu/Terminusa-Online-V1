from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import logging

from game_systems import GameManager
from models import User, Wallet, Inventory, InventoryItem, Item, Gate, MagicBeast, Guild, GuildMember
from db_setup import db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class GameState:
    active_gates: Dict[int, Dict]  # gate_id -> gate_state
    active_parties: Dict[int, Dict]  # party_id -> party_state
    active_trades: Dict[int, Dict]  # trade_id -> trade_state
    active_guild_quests: Dict[int, Dict]  # quest_id -> quest_state

class MainGameManager:
    def __init__(self):
        self.game_systems = GameManager()
        self.game_state = GameState(
            active_gates={},
            active_parties={},
            active_trades={},
            active_guild_quests={}
        )

    def process_command(self, command: str, user_id: int, params: Dict) -> Dict:
        """Process a game command from a user"""
        try:
            logger.debug(f"Processing command '{command}' for user {user_id} with params: {params}")
            
            # Get user from database
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': 'User not found'}
            
            # Route command to appropriate handler
            if command.startswith('gate_'):
                return self._handle_gate_command(command, user, params)
            elif command.startswith('party_'):
                return self._handle_party_command(command, user, params)
            elif command.startswith('trade_'):
                return self._handle_trade_command(command, user, params)
            elif command.startswith('guild_'):
                return self._handle_guild_command(command, user, params)
            elif command.startswith('shop_'):
                return self._handle_shop_command(command, user, params)
            elif command.startswith('gacha_'):
                return self._handle_gacha_command(command, user, params)
            elif command.startswith('token_'):
                return self._handle_token_command(command, user, params)
            else:
                return {'status': 'error', 'message': 'Unknown command'}
                
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _handle_gate_command(self, command: str, user: User, params: Dict) -> Dict:
        """Handle gate-related commands"""
        try:
            if command == 'gate_enter':
                gate_id = params.get('gate_id')
                party_id = params.get('party_id')
                
                gate = Gate.query.get(gate_id)
                if not gate:
                    return {'status': 'error', 'message': 'Gate not found'}
                
                # Get party members if in party
                party_members = []
                if party_id:
                    party_members = self._get_party_members(party_id, user.id)
                
                # Process gate entry
                result = self.game_systems.process_gate_entry(user, gate, party_members)
                
                if result['status'] == 'success':
                    # Update game state
                    gate_state = {
                        'gate_id': gate_id,
                        'party_id': party_id,
                        'start_time': datetime.utcnow(),
                        'players': [user.id] + [m.id for m in party_members],
                        'monsters': result['combat_results'].get('monsters', [])
                    }
                    self.game_state.active_gates[gate_id] = gate_state
                    
                    # Commit changes to database
                    db.session.commit()
                
                return result
                
            elif command == 'gate_exit':
                gate_id = params.get('gate_id')
                
                if gate_id not in self.game_state.active_gates:
                    return {'status': 'error', 'message': 'Gate not active'}
                
                # Clean up gate state
                del self.game_state.active_gates[gate_id]
                
                return {'status': 'success', 'message': 'Exited gate successfully'}
                
            else:
                return {'status': 'error', 'message': 'Unknown gate command'}
                
        except Exception as e:
            logger.error(f"Error handling gate command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _handle_party_command(self, command: str, user: User, params: Dict) -> Dict:
        """Handle party-related commands"""
        try:
            if command == 'party_create':
                name = params.get('name', f"{user.username}'s Party")
                max_members = params.get('max_members', 10)
                
                # Create new party
                party = {
                    'id': len(self.game_state.active_parties) + 1,
                    'name': name,
                    'leader_id': user.id,
                    'members': [user.id],
                    'max_members': max_members,
                    'status': 'recruiting'
                }
                self.game_state.active_parties[party['id']] = party
                
                return {
                    'status': 'success',
                    'party_id': party['id'],
                    'message': 'Party created successfully'
                }
                
            elif command == 'party_invite':
                party_id = params.get('party_id')
                target_user_id = params.get('user_id')
                
                party = self.game_state.active_parties.get(party_id)
                if not party:
                    return {'status': 'error', 'message': 'Party not found'}
                
                if party['leader_id'] != user.id:
                    return {'status': 'error', 'message': 'Only party leader can invite'}
                
                if len(party['members']) >= party['max_members']:
                    return {'status': 'error', 'message': 'Party is full'}
                
                # Add member to party
                party['members'].append(target_user_id)
                
                return {'status': 'success', 'message': 'Player invited successfully'}
                
            elif command == 'party_leave':
                party_id = params.get('party_id')
                
                party = self.game_state.active_parties.get(party_id)
                if not party:
                    return {'status': 'error', 'message': 'Party not found'}
                
                if user.id not in party['members']:
                    return {'status': 'error', 'message': 'Not in party'}
                
                # Remove from party
                party['members'].remove(user.id)
                
                # If leader leaves, assign new leader or disband
                if user.id == party['leader_id']:
                    if party['members']:
                        party['leader_id'] = party['members'][0]
                    else:
                        del self.game_state.active_parties[party_id]
                
                return {'status': 'success', 'message': 'Left party successfully'}
                
            else:
                return {'status': 'error', 'message': 'Unknown party command'}
                
        except Exception as e:
            logger.error(f"Error handling party command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _handle_trade_command(self, command: str, user: User, params: Dict) -> Dict:
        """Handle trade-related commands"""
        try:
            if command == 'trade_create':
                item_id = params.get('item_id')
                quantity = params.get('quantity', 1)
                price = params.get('price')
                currency = params.get('currency')
                
                result = self.game_systems.process_marketplace_action(
                    'create_listing',
                    user,
                    item_id=item_id,
                    quantity=quantity,
                    price=price,
                    currency=currency
                )
                
                if result['status'] == 'success':
                    # Update game state
                    trade_id = result['listing_id']
                    self.game_state.active_trades[trade_id] = {
                        'seller_id': user.id,
                        'item_id': item_id,
                        'quantity': quantity,
                        'price': price,
                        'currency': currency,
                        'status': 'active'
                    }
                
                return result
                
            elif command == 'trade_accept':
                trade_id = params.get('trade_id')
                
                result = self.game_systems.process_marketplace_action(
                    'purchase',
                    user,
                    listing_id=trade_id
                )
                
                if result['status'] == 'success':
                    # Update trade state
                    if trade_id in self.game_state.active_trades:
                        self.game_state.active_trades[trade_id]['status'] = 'completed'
                
                return result
                
            else:
                return {'status': 'error', 'message': 'Unknown trade command'}
                
        except Exception as e:
            logger.error(f"Error handling trade command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _handle_guild_command(self, command: str, user: User, params: Dict) -> Dict:
        """Handle guild-related commands"""
        try:
            if command == 'guild_create':
                name = params.get('name')
                
                # Check if user has enough currency
                wallet = Wallet.query.filter_by(user_id=user.id).first()
                if not wallet:
                    return {'status': 'error', 'message': 'Wallet not found'}
                
                required_exons = 1000
                required_crystals = 1000
                
                if wallet.exons < required_exons or wallet.crystals < required_crystals:
                    return {
                        'status': 'error',
                        'message': f'Insufficient funds. Required: {required_exons} Exons and {required_crystals} Crystals'
                    }
                
                # Create guild
                guild = Guild(
                    name=name,
                    leader_id=user.id,
                    level=1,
                    exons_balance=0,
                    crystals_balance=0
                )
                db.session.add(guild)
                
                # Create guild membership
                membership = GuildMember(
                    guild=guild,
                    user=user,
                    role='leader'
                )
                db.session.add(membership)
                
                # Deduct currency
                wallet.exons -= required_exons
                wallet.crystals -= required_crystals
                
                db.session.commit()
                
                return {
                    'status': 'success',
                    'guild_id': guild.id,
                    'message': 'Guild created successfully'
                }
                
            elif command == 'guild_join':
                guild_id = params.get('guild_id')
                
                guild = Guild.query.get(guild_id)
                if not guild:
                    return {'status': 'error', 'message': 'Guild not found'}
                
                if user.guild_membership:
                    return {'status': 'error', 'message': 'Already in a guild'}
                
                # Create membership
                membership = GuildMember(
                    guild=guild,
                    user=user,
                    role='member'
                )
                db.session.add(membership)
                db.session.commit()
                
                return {'status': 'success', 'message': 'Joined guild successfully'}
                
            else:
                return {'status': 'error', 'message': 'Unknown guild command'}
                
        except Exception as e:
            logger.error(f"Error handling guild command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _handle_shop_command(self, command: str, user: User, params: Dict) -> Dict:
        """Handle shop-related commands"""
        try:
            if command == 'shop_buy':
                item_key = params.get('item_key')
                quantity = params.get('quantity', 1)
                
                result = self.game_systems.shop_system.purchase_item(
                    user,
                    item_key,
                    quantity
                )
                
                if result['status'] == 'success':
                    # Update inventory (actual implementation would handle this)
                    pass
                
                return result
                
            else:
                return {'status': 'error', 'message': 'Unknown shop command'}
                
        except Exception as e:
            logger.error(f"Error handling shop command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _handle_gacha_command(self, command: str, user: User, params: Dict) -> Dict:
        """Handle gacha-related commands"""
        try:
            if command == 'gacha_pull':
                gacha_type = params.get('type')
                pulls = params.get('pulls', 1)
                
                result = self.game_systems.process_gacha_pull(
                    user,
                    gacha_type,
                    pulls
                )
                
                if result['status'] == 'success':
                    # Update inventory with obtained items
                    pass
                
                return result
                
            else:
                return {'status': 'error', 'message': 'Unknown gacha command'}
                
        except Exception as e:
            logger.error(f"Error handling gacha command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _handle_token_command(self, command: str, user: User, params: Dict) -> Dict:
        """Handle token-related commands"""
        try:
            if command == 'token_swap':
                from_currency = params.get('from_currency')
                to_currency = params.get('to_currency')
                amount = params.get('amount')
                
                result = self.game_systems.process_token_swap(
                    user,
                    from_currency,
                    to_currency,
                    amount
                )
                
                if result['status'] == 'success':
                    # Update wallet balances
                    wallet = Wallet.query.filter_by(user_id=user.id).first()
                    if not wallet:
                        return {'status': 'error', 'message': 'Wallet not found'}
                    
                    # Apply the swap (actual implementation would handle blockchain transactions)
                    if from_currency == 'SOLANA':
                        wallet.sol_balance -= amount
                        wallet.exons += result['to_amount']
                    elif from_currency == 'EXON':
                        wallet.exons -= amount
                        wallet.crystals += result['to_amount']
                    
                    db.session.commit()
                
                return result
                
            else:
                return {'status': 'error', 'message': 'Unknown token command'}
                
        except Exception as e:
            logger.error(f"Error handling token command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _get_party_members(self, party_id: int, exclude_user_id: int) -> List[User]:
        """Get all party members except the specified user"""
        party = self.game_state.active_parties.get(party_id)
        if not party:
            return []
            
        member_ids = [mid for mid in party['members'] if mid != exclude_user_id]
        return User.query.filter(User.id.in_(member_ids)).all()

    def update_game_state(self):
        """Update global game state (called periodically)"""
        try:
            current_time = datetime.utcnow()
            
            # Clean up expired gates
            expired_gates = []
            for gate_id, gate_state in self.game_state.active_gates.items():
                if (current_time - gate_state['start_time']).total_seconds() > 3600:  # 1 hour timeout
                    expired_gates.append(gate_id)
            
            for gate_id in expired_gates:
                del self.game_state.active_gates[gate_id]
            
            # Clean up inactive parties
            inactive_parties = []
            for party_id, party_state in self.game_state.active_parties.items():
                if not party_state['members']:
                    inactive_parties.append(party_id)
            
            for party_id in inactive_parties:
                del self.game_state.active_parties[party_id]
            
            # Clean up completed trades
            completed_trades = []
            for trade_id, trade_state in self.game_state.active_trades.items():
                if trade_state['status'] == 'completed':
                    completed_trades.append(trade_id)
            
            for trade_id in completed_trades:
                del self.game_state.active_trades[trade_id]
            
            logger.debug("Game state updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating game state: {str(e)}", exc_info=True)
