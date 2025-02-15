from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from datetime import datetime

from game_manager import MainGameManager
from models import User, Wallet, Inventory, Item, Gate, Guild
from db_setup import db

app = Flask(__name__)
game_manager = MainGameManager()

# ======== WEB ROUTES ========
@app.route('/')
def home():
    """Main website landing page"""
    return render_template('index.html')

@app.route('/play')
@jwt_required()
def play():
    """Game play area"""
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('home'))
    
    return render_template('play.html', user=user)

# ======== MARKETPLACE ROUTES ========
@app.route('/marketplace')
@jwt_required()
def marketplace():
    """Marketplace overview"""
    try:
        # Get active listings
        listings = game_manager.game_state.active_trades
        
        # Get user's wallet
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        wallet = Wallet.query.filter_by(user_id=user.id).first() if user else None
        
        return render_template(
            'marketplace.html',
            listings=listings,
            wallet=wallet
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/marketplace/create', methods=['POST'])
@jwt_required()
def create_listing():
    """Create a new marketplace listing"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        result = game_manager.process_command(
            'trade_create',
            user.id,
            request.json
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/marketplace/purchase/<int:listing_id>', methods=['POST'])
@jwt_required()
def purchase_listing(listing_id):
    """Purchase an item from the marketplace"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        result = game_manager.process_command(
            'trade_accept',
            user.id,
            {'trade_id': listing_id}
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ======== TOKEN SWAP ROUTES ========
@app.route('/swap')
@jwt_required()
def token_swap():
    """Token swap interface"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        wallet = Wallet.query.filter_by(user_id=user.id).first() if user else None
        
        return render_template(
            'swap.html',
            wallet=wallet,
            swap_rates=game_manager.game_systems.token_system.swap_rates
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/swap/execute', methods=['POST'])
@jwt_required()
def execute_swap():
    """Execute a token swap"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        result = game_manager.process_command(
            'token_swap',
            user.id,
            request.json
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ======== GUILD ROUTES ========
@app.route('/guilds')
@jwt_required()
def guilds():
    """Guild listing and management"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        
        # Get all guilds and user's guild if any
        all_guilds = Guild.query.all()
        user_guild = user.guild_membership.guild if user and user.guild_membership else None
        
        return render_template(
            'guilds.html',
            guilds=all_guilds,
            user_guild=user_guild
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/guilds/create', methods=['POST'])
@jwt_required()
def create_guild():
    """Create a new guild"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        result = game_manager.process_command(
            'guild_create',
            user.id,
            request.json
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/guilds/join/<int:guild_id>', methods=['POST'])
@jwt_required()
def join_guild(guild_id):
    """Join an existing guild"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        result = game_manager.process_command(
            'guild_join',
            user.id,
            {'guild_id': guild_id}
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ======== GATE ROUTES ========
@app.route('/gates')
@jwt_required()
def gates():
    """Gate listing and status"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        
        # Get available gates
        all_gates = Gate.query.all()
        available_gates = []
        
        for gate in all_gates:
            can_enter, message = game_manager.game_systems.gate_system.can_enter_gate(user, gate)
            if can_enter:
                available_gates.append({
                    'id': gate.id,
                    'name': gate.name,
                    'grade': gate.grade,
                    'min_level': gate.min_level,
                    'max_players': gate.max_players,
                    'crystal_reward': gate.crystal_reward
                })
        
        # Get active gates
        active_gates = {
            gate_id: state for gate_id, state in game_manager.game_state.active_gates.items()
            if user.id in state['players']
        }
        
        return render_template(
            'gates.html',
            available_gates=available_gates,
            active_gates=active_gates
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/gates/<int:gate_id>/enter', methods=['POST'])
@jwt_required()
def enter_gate(gate_id):
    """Enter a gate"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        params = request.json or {}
        params['gate_id'] = gate_id
        
        result = game_manager.process_command(
            'gate_enter',
            user.id,
            params
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ======== PARTY ROUTES ========
@app.route('/party/create', methods=['POST'])
@jwt_required()
def create_party():
    """Create a new party"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        result = game_manager.process_command(
            'party_create',
            user.id,
            request.json
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/party/<int:party_id>/invite', methods=['POST'])
@jwt_required()
def invite_to_party(party_id):
    """Invite a player to party"""
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        params = request.json or {}
        params['party_id'] = party_id
        
        result = game_manager.process_command(
            'party_invite',
            user.id,
            params
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/party/list')
@jwt_required()
def list_parties():
    """List available parties"""
    try:
        parties = game_manager.game_state.active_parties
        party_list = []
        
        for party_id, party in parties.items():
            if party['status'] == 'recruiting':
                members = User.query.filter(User.id.in_(party['members'])).all()
                party_list.append({
                    'id': party_id,
                    'name': party['name'],
                    'leader': User.query.get(party['leader_id']).username,
                    'members': len(members),
                    'max_members': party['max_members']
                })
        
        return jsonify({
            'status': 'success',
            'parties': party_list
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('WEBAPP_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
