from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from decimal import Decimal

from models import db, User, Guild, GuildMember, GuildQuest, GuildTransaction
from game_systems.guild_system import GuildSystem

guild_bp = Blueprint('guild', __name__)
guild_system = None

@guild_bp.record
def record_guild_system(state):
    """Initialize guild system with app context"""
    global guild_system
    guild_system = GuildSystem(state.app.websocket)

# Guild Management Routes
@guild_bp.route('/api/guild/create', methods=['POST'])
@login_required
def create_guild():
    """Create a new guild"""
    data = request.get_json()
    
    # Validate required fields
    if not all(key in data for key in ['name', 'description']):
        return jsonify({
            "success": False,
            "message": "Missing required fields"
        }), 400
        
    result = guild_system.create_guild(
        leader=current_user,
        name=data['name'],
        description=data['description']
    )
    
    return jsonify(result)

@guild_bp.route('/api/guild/<int:guild_id>/settings', methods=['PUT'])
@login_required
def update_settings(guild_id):
    """Update guild settings"""
    data = request.get_json()
    
    result = guild_system.update_settings(
        guild_id=guild_id,
        settings=data,
        user=current_user
    )
    
    return jsonify(result)

@guild_bp.route('/api/guild/<int:guild_id>/member/<int:member_id>', methods=['POST'])
@login_required
def manage_member(guild_id, member_id):
    """Manage guild member (promote, demote, kick)"""
    data = request.get_json()
    action = data.get('action')
    
    if action not in ['promote', 'demote', 'kick']:
        return jsonify({
            "success": False,
            "message": "Invalid action"
        }), 400
        
    result = guild_system.manage_member(
        guild_id=guild_id,
        target_id=member_id,
        action=action,
        user=current_user
    )
    
    return jsonify(result)

# Guild Treasury Routes
@guild_bp.route('/api/guild/<int:guild_id>/treasury/withdraw', methods=['POST'])
@login_required
def withdraw_funds():
    """Withdraw funds from guild treasury"""
    data = request.get_json()
    
    if not all(key in data for key in ['currency', 'amount']):
        return jsonify({
            "success": False,
            "message": "Missing required fields"
        }), 400
        
    guild = Guild.query.get(guild_id)
    if not guild:
        return jsonify({
            "success": False,
            "message": "Guild not found"
        }), 404
        
    if not current_user.can_manage_treasury(guild):
        return jsonify({
            "success": False,
            "message": "Insufficient permissions"
        }), 403
        
    try:
        amount = Decimal(str(data['amount']))
        currency = data['currency']
        
        if currency == 'crystals':
            if amount > guild.crystal_balance:
                return jsonify({
                    "success": False,
                    "message": "Insufficient crystal balance"
                }), 400
            guild.crystal_balance -= amount
            
        elif currency == 'exons':
            if amount > guild.exon_balance:
                return jsonify({
                    "success": False,
                    "message": "Insufficient exon balance"
                }), 400
            guild.exon_balance -= amount
            
        else:
            return jsonify({
                "success": False,
                "message": "Invalid currency"
            }), 400
            
        # Record transaction
        transaction = GuildTransaction(
            guild_id=guild.id,
            transaction_type='withdrawal',
            crystal_amount=amount if currency == 'crystals' else 0,
            exon_amount=amount if currency == 'exons' else 0,
            initiated_by=current_user.id,
            description=f"Treasury withdrawal by {current_user.username}"
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Emit treasury update event
        guild_system.event_system.emit_event({
            'type': 'treasury_updated',
            'guild_id': guild.id,
            'crystal_balance': str(guild.crystal_balance),
            'exon_balance': str(guild.exon_balance),
            'transaction': transaction.to_dict()
        })
        
        return jsonify({
            "success": True,
            "message": f"Withdrew {amount} {currency}",
            "transaction": transaction.to_dict()
        })
        
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid amount"
        }), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# Guild Quest Routes
@guild_bp.route('/api/guild/<int:guild_id>/quests')
@login_required
def get_quests(guild_id):
    """Get guild quests"""
    guild = Guild.query.get(guild_id)
    if not guild:
        return jsonify({
            "success": False,
            "message": "Guild not found"
        }), 404
        
    active_quests = GuildQuest.query.filter_by(
        guild_id=guild_id,
        status='active'
    ).all()
    
    completed_quests = GuildQuest.query.filter_by(
        guild_id=guild_id,
        status='completed'
    ).order_by(GuildQuest.completed_at.desc()).limit(10).all()
    
    return jsonify({
        "success": True,
        "active_quests": [quest.to_dict() for quest in active_quests],
        "completed_quests": [quest.to_dict() for quest in completed_quests]
    })

@guild_bp.route('/api/guild/<int:guild_id>/quest/<int:quest_id>/complete', methods=['POST'])
@login_required
def complete_quest(guild_id, quest_id):
    """Complete a guild quest"""
    guild = Guild.query.get(guild_id)
    if not guild:
        return jsonify({
            "success": False,
            "message": "Guild not found"
        }), 404
        
    quest = GuildQuest.query.get(quest_id)
    if not quest:
        return jsonify({
            "success": False,
            "message": "Quest not found"
        }), 404
        
    if quest.guild_id != guild_id:
        return jsonify({
            "success": False,
            "message": "Quest does not belong to guild"
        }), 403
        
    if quest.status != 'active':
        return jsonify({
            "success": False,
            "message": "Quest is not active"
        }), 400
        
    try:
        # Process quest completion
        quest.status = 'completed'
        quest.completed_at = datetime.utcnow()
        quest.completed_by = current_user.id
        
        # Process rewards
        guild_system.process_quest_rewards(guild, quest, quest.rewards)
        
        db.session.commit()
        
        # Emit quest completion event
        guild_system.event_system.emit_event({
            'type': 'quest_completed',
            'guild_id': guild.id,
            'quest': quest.to_dict()
        })
        
        return jsonify({
            "success": True,
            "message": "Quest completed successfully",
            "quest": quest.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# Error Handlers
@guild_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': str(error)
    }), 400

@guild_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'message': 'Insufficient permissions'
    }), 403

@guild_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404

@guild_bp.errorhandler(500)
def server_error(error):
    current_app.logger.error(f'Server Error: {error}')
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500
