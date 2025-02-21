from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from decimal import Decimal
from datetime import datetime

from models import db, User, Mount, Pet, Transaction
from game_systems.marketplace_system import MarketplaceSystem
from game_systems.gacha_system import GachaSystem
from game_systems.currency_system import CurrencySystem

marketplace_bp = Blueprint('marketplace', __name__)
marketplace_system = MarketplaceSystem()
gacha_system = GachaSystem()
currency_system = CurrencySystem()

# Marketplace Routes
@marketplace_bp.route('/api/marketplace/listings')
@login_required
def get_listings():
    """Get filtered marketplace listings"""
    item_type = request.args.get('itemType')
    currency = request.args.get('currency')
    min_price = request.args.get('minPrice')
    max_price = request.args.get('maxPrice')
    
    if min_price:
        min_price = Decimal(min_price)
    if max_price:
        max_price = Decimal(max_price)
        
    listings = marketplace_system.get_listings(
        currency=currency,
        item_type=item_type,
        min_price=min_price,
        max_price=max_price
    )
    
    return jsonify(listings)

@marketplace_bp.route('/api/marketplace/mounts')
@login_required
def get_mount_listings():
    """Get mount listings"""
    rarity = request.args.get('rarity')
    listings = marketplace_system.get_listings(item_type='mount', rarity=rarity)
    return jsonify(listings)

@marketplace_bp.route('/api/marketplace/pets')
@login_required
def get_pet_listings():
    """Get pet listings"""
    rarity = request.args.get('rarity')
    listings = marketplace_system.get_listings(item_type='pet', rarity=rarity)
    return jsonify(listings)

@marketplace_bp.route('/api/marketplace/my-listings')
@login_required
def get_my_listings():
    """Get current user's listings"""
    listings = marketplace_system.get_listings(seller_id=current_user.id)
    return jsonify(listings)

@marketplace_bp.route('/api/marketplace/create', methods=['POST'])
@login_required
def create_listing():
    """Create a new marketplace listing"""
    data = request.get_json()
    
    result = marketplace_system.create_listing(
        seller=current_user,
        item_id=data['itemId'],
        quantity=data['quantity'],
        price=Decimal(str(data['price'])),
        currency=data['currency']
    )
    
    return jsonify(result)

@marketplace_bp.route('/api/marketplace/purchase', methods=['POST'])
@login_required
def purchase_listing():
    """Purchase an item from the marketplace"""
    data = request.get_json()
    
    result = marketplace_system.purchase_listing(
        buyer=current_user,
        listing_id=data['listingId']
    )
    
    return jsonify(result)

@marketplace_bp.route('/api/marketplace/cancel', methods=['POST'])
@login_required
def cancel_listing():
    """Cancel a marketplace listing"""
    data = request.get_json()
    
    result = marketplace_system.cancel_listing(
        seller=current_user,
        listing_id=data['listingId']
    )
    
    return jsonify(result)

# Gacha Routes
@marketplace_bp.route('/api/gacha/roll', methods=['POST'])
@login_required
def roll_gacha():
    """Roll the gacha system"""
    data = request.get_json()
    gacha_type = data['type']  # 'mount' or 'pet'
    amount = data.get('amount', 1)
    
    if gacha_type == 'mount':
        result = gacha_system.roll_mount(current_user, amount)
    else:
        result = gacha_system.roll_pet(current_user, amount)
        
    return jsonify(result)

@marketplace_bp.route('/api/gacha/rates')
@login_required
def get_gacha_rates():
    """Get current gacha rates for the user"""
    mount_rates = gacha_system.get_rates(current_user, 'mount')
    pet_rates = gacha_system.get_rates(current_user, 'pet')
    
    return jsonify({
        'mount_rates': mount_rates,
        'pet_rates': pet_rates
    })

@marketplace_bp.route('/api/gacha/pity')
@login_required
def get_pity_info():
    """Get pity system information"""
    pity_info = gacha_system.get_pity_info(current_user)
    return jsonify(pity_info)

# Currency Routes
@marketplace_bp.route('/api/user/currency')
@login_required
def get_currency():
    """Get user's currency balances"""
    return jsonify({
        'solana_balance': str(current_user.solana_balance),
        'exons_balance': str(current_user.exons_balance),
        'crystals': current_user.crystals
    })

@marketplace_bp.route('/api/currency/swap', methods=['POST'])
@login_required
def swap_currency():
    """Swap between currencies"""
    data = request.get_json()
    
    result = currency_system.swap_currency(
        user=current_user,
        from_currency=data['fromCurrency'],
        to_currency=data['toCurrency'],
        amount=Decimal(str(data['amount']))
    )
    
    return jsonify(result)

# Error Handlers
@marketplace_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': str(error)
    }), 400

@marketplace_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404

@marketplace_bp.errorhandler(500)
def server_error(error):
    current_app.logger.error(f'Server Error: {error}')
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

# Register blueprint in app.py
# app.register_blueprint(marketplace_bp)
