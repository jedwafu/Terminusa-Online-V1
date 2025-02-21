from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from game_systems.inventory_system import InventorySystem

inventory_bp = Blueprint('inventory', __name__)
inventory_system = InventorySystem()

@inventory_bp.route('/api/inventory')
@login_required
def get_inventory():
    """Get user's complete inventory"""
    result = inventory_system.get_inventory(current_user)
    return jsonify(result)

@inventory_bp.route('/api/inventory/mount/equip', methods=['POST'])
@login_required
def equip_mount():
    """Equip a mount"""
    data = request.get_json()
    mount_id = data.get('mountId')
    
    result = inventory_system.equip_mount(current_user, mount_id)
    return jsonify(result)

@inventory_bp.route('/api/inventory/pet/activate', methods=['POST'])
@login_required
def activate_pet():
    """Activate a pet"""
    data = request.get_json()
    pet_id = data.get('petId')
    
    result = inventory_system.activate_pet(current_user, pet_id)
    return jsonify(result)

@inventory_bp.route('/api/inventory/expand', methods=['POST'])
@login_required
def expand_inventory():
    """Expand inventory slots"""
    data = request.get_json()
    amount = data.get('amount', 10)
    
    result = inventory_system.expand_inventory(current_user, amount)
    return jsonify(result)

@inventory_bp.route('/api/inventory/mount/stats')
@login_required
def get_mount_stats():
    """Get current mount stats and bonuses"""
    result = inventory_system.get_mount_stats(current_user)
    return jsonify(result)

@inventory_bp.route('/api/inventory/pet/abilities')
@login_required
def get_pet_abilities():
    """Get current pet abilities and cooldowns"""
    result = inventory_system.get_pet_abilities(current_user)
    return jsonify(result)

@inventory_bp.route('/api/inventory/repair', methods=['POST'])
@login_required
def repair_equipment():
    """Repair equipment"""
    data = request.get_json()
    item_id = data.get('itemId')
    
    result = inventory_system.repair_equipment(current_user, item_id)
    return jsonify(result)

@inventory_bp.route('/api/inventory/mount/unequip', methods=['POST'])
@login_required
def unequip_mount():
    """Unequip current mount"""
    mount = Mount.query.filter_by(user_id=current_user.id, is_equipped=True).first()
    if mount:
        mount.is_equipped = False
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Unequipped {mount.name}"
        })
    return jsonify({
        "success": False,
        "message": "No mount equipped"
    })

@inventory_bp.route('/api/inventory/pet/deactivate', methods=['POST'])
@login_required
def deactivate_pet():
    """Deactivate current pet"""
    pet = Pet.query.filter_by(user_id=current_user.id, is_active=True).first()
    if pet:
        pet.is_active = False
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Deactivated {pet.name}"
        })
    return jsonify({
        "success": False,
        "message": "No pet active"
    })

@inventory_bp.route('/api/inventory/stats')
@login_required
def get_inventory_stats():
    """Get inventory statistics"""
    try:
        total_items = Item.query.filter_by(user_id=current_user.id).count()
        total_mounts = Mount.query.filter_by(user_id=current_user.id).count()
        total_pets = Pet.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_items": total_items,
                "total_mounts": total_mounts,
                "total_pets": total_pets,
                "slots_used": total_items,
                "slots_total": current_user.inventory_slots,
                "slots_available": current_user.inventory_slots - total_items
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to get inventory stats: {str(e)}"
        })

# Error Handlers
@inventory_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': str(error)
    }), 400

@inventory_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404

@inventory_bp.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

# Register blueprint in app.py
# app.register_blueprint(inventory_bp)
