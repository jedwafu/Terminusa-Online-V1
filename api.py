from flask import Blueprint, jsonify, request
from models import User, Item, Listing, Transaction
from database import db
from game_systems.currency_system import CurrencySystem
from game_systems.marketplace_system import MarketplaceSystem
from game_systems.gacha_system import GachaSystem
from flask_jwt_extended import jwt_required, get_jwt_identity

api = Blueprint('api', __name__)
currency_system = CurrencySystem()
marketplace_system = MarketplaceSystem(currency_system)
gacha_system = GachaSystem()

@api.route('/api/marketplace/listings', methods=['GET'])
def get_listings():
    """Get marketplace listings with filters"""
    try:
        filters = {
            'item_type': request.args.get('itemType'),
            'currency': request.args.get('currency'),
            'min_price': request.args.get('minPrice'),
            'max_price': request.args.get('maxPrice')
        }
        listings = marketplace_system.get_listings(filters)
        return jsonify([listing.to_dict() for listing in listings])
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/api/marketplace/purchase', methods=['POST'])
@jwt_required()
def purchase_listing():
    """Purchase a marketplace listing"""
    try:
        data = request.get_json()
        user = User.query.filter_by(username=get_jwt_identity()).first()
        result = marketplace_system.purchase_listing(user, data['listingId'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/api/marketplace/create', methods=['POST'])
@jwt_required()
def create_listing():
    """Create a new marketplace listing"""
    try:
        data = request.get_json()
        user = User.query.filter_by(username=get_jwt_identity()).first()
        result = marketplace_system.create_listing(user, data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/api/currency/swap', methods=['POST'])
@jwt_required()
def swap_currency():
    """Swap between currencies"""
    try:
        data = request.get_json()
        user = User.query.filter_by(username=get_jwt_identity()).first()
        result = currency_system.swap_currency(
            user,
            data['from_currency'],
            data['to_currency'],
            data['amount']
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/api/gacha/roll', methods=['POST'])
@jwt_required()
def roll_gacha():
    """Roll the gacha system"""
    try:
        data = request.get_json()
        user = User.query.filter_by(username=get_jwt_identity()).first()
        result = gacha_system.roll_gacha(user, data['type'], data['amount'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/api/user/currency', methods=['GET'])
@jwt_required()
def get_user_currency():
    """Get user's currency balances"""
    try:
        user = User.query.filter_by(username=get_jwt_identity()).first()
        return jsonify({
            'solana_balance': user.solana_balance,
            'exons_balance': user.exons_balance,
            'crystals': user.crystals
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/api/gacha/pity', methods=['GET'])
@jwt_required()
def get_pity_info():
    """Get gacha pity information"""
    try:
        user = User.query.filter_by(username=get_jwt_identity()).first()
        result = gacha_system.get_pity_info(user)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
