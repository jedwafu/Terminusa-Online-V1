from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime

from models import db, Guild, GuildMember, User
from game_systems.guild_war import GuildWar
from game_systems.achievement_triggers import AchievementTriggers

guild_war_bp = Blueprint('guild_war', __name__)
guild_war_system = None
achievement_triggers = None

@guild_war_bp.record
def record_guild_war_system(state):
    """Initialize guild war system with app context"""
    global guild_war_system, achievement_triggers
    guild_war_system = GuildWar(state.app.websocket)
    achievement_triggers = AchievementTriggers(state.app.websocket)

# War Declaration Routes
@guild_war_bp.route('/api/guild/war/declare', methods=['POST'])
@login_required
def declare_war():
    """Declare war on another guild"""
    try:
        data = request.get_json()
        target_guild_id = data.get('target_guild_id')

        if not target_guild_id:
            return jsonify({
                "success": False,
                "message": "Target guild not specified"
            }), 400

        # Get challenger and target guilds
        challenger = Guild.query.get(current_user.guild_id)
        target = Guild.query.get(target_guild_id)

        if not challenger or not target:
            return jsonify({
                "success": False,
                "message": "Invalid guild"
            }), 404

        # Check if user has permission
        if not current_user.id == challenger.leader_id:
            return jsonify({
                "success": False,
                "message": "Only guild leader can declare war"
            }), 403

        result = guild_war_system.initiate_war(challenger, target)
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"War declaration error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to declare war"
        }), 500

@guild_war_bp.route('/api/guild/war/participants', methods=['POST'])
@login_required
def update_participants():
    """Update war participants"""
    try:
        data = request.get_json()
        war_id = data.get('war_id')
        participants = data.get('participants', [])

        if not war_id:
            return jsonify({
                "success": False,
                "message": "War ID not specified"
            }), 400

        guild = Guild.query.get(current_user.guild_id)
        if not guild:
            return jsonify({
                "success": False,
                "message": "Guild not found"
            }), 404

        # Check if user can manage participants
        if not (current_user.id == guild.leader_id or 
                current_user.guild_rank in ['officer']):
            return jsonify({
                "success": False,
                "message": "Insufficient permissions"
            }), 403

        result = guild_war_system.register_participants(
            guild=guild,
            member_ids=participants,
            war_id=war_id
        )
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Participant update error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to update participants"
        }), 500

# Territory Control Routes
@guild_war_bp.route('/api/guild/war/territory/attack', methods=['POST'])
@login_required
def attack_territory():
    """Attack a territory"""
    try:
        data = request.get_json()
        territory_id = data.get('territory_id')

        if not territory_id:
            return jsonify({
                "success": False,
                "message": "Territory not specified"
            }), 400

        # Check if user is war participant
        war_data = guild_war_system._get_war_data(data.get('war_id'))
        if not war_data or str(current_user.id) not in war_data['participants'].get(str(current_user.guild_id), []):
            return jsonify({
                "success": False,
                "message": "Not a war participant"
            }), 403

        event_data = {
            'type': 'territory_attack',
            'attacker_guild_id': current_user.guild_id,
            'territory_id': territory_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        result = guild_war_system.process_combat_event(
            war_id=data.get('war_id'),
            event_data=event_data
        )
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Territory attack error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to process attack"
        }), 500

@guild_war_bp.route('/api/guild/war/territory/reinforce', methods=['POST'])
@login_required
def reinforce_territory():
    """Reinforce a territory"""
    try:
        data = request.get_json()
        territory_id = data.get('territory_id')

        if not territory_id:
            return jsonify({
                "success": False,
                "message": "Territory not specified"
            }), 400

        # Check if user is war participant
        war_data = guild_war_system._get_war_data(data.get('war_id'))
        if not war_data or str(current_user.id) not in war_data['participants'].get(str(current_user.guild_id), []):
            return jsonify({
                "success": False,
                "message": "Not a war participant"
            }), 403

        event_data = {
            'type': 'territory_reinforce',
            'guild_id': current_user.guild_id,
            'territory_id': territory_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        result = guild_war_system.process_combat_event(
            war_id=data.get('war_id'),
            event_data=event_data
        )
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Territory reinforcement error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to reinforce territory"
        }), 500

# War Status Routes
@guild_war_bp.route('/api/guild/war/<war_id>/status')
@login_required
def get_war_status(war_id):
    """Get current war status"""
    try:
        war_data = guild_war_system._get_war_data(war_id)
        if not war_data:
            return jsonify({
                "success": False,
                "message": "War not found"
            }), 404

        # Check if user's guild is involved in the war
        if str(current_user.guild_id) not in [
            str(war_data['challenger_id']),
            str(war_data['target_id'])
        ]:
            return jsonify({
                "success": False,
                "message": "Not authorized to view this war"
            }), 403

        return jsonify({
            "success": True,
            "war_data": war_data
        })

    except Exception as e:
        current_app.logger.error(f"War status error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get war status"
        }), 500

@guild_war_bp.route('/api/guild/war/history')
@login_required
def get_war_history():
    """Get guild's war history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Get wars where the guild was involved
        wars = guild_war_system.get_guild_wars(
            guild_id=current_user.guild_id,
            page=page,
            per_page=per_page
        )

        return jsonify({
            "success": True,
            "wars": wars
        })

    except Exception as e:
        current_app.logger.error(f"War history error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get war history"
        }), 500

# Error Handlers
@guild_war_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': str(error)
    }), 400

@guild_war_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'message': 'Insufficient permissions'
    }), 403

@guild_war_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404

@guild_war_bp.errorhandler(500)
def server_error(error):
    current_app.logger.error(f'Server Error: {error}')
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500
