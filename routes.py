from flask import jsonify, request, render_template, send_from_directory, make_response
from app import app, db
from models import User, Transaction, ChatMessage, Wallet, Inventory, Item, Gate, Guild
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request, create_access_token
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from email_service import email_service
import os
from functools import wraps

# Root route
@app.route('/')
def index():
    """Main landing page"""
    try:
        response = make_response(render_template('index.html'))
        response.headers['Content-Type'] = 'text/html'
        return response
    except Exception as e:
        app.logger.error(f"Error rendering index page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

# Static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Health check route
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

# Page routes
@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/play')
@jwt_required()
def play_page():
    return render_template('play.html')

@app.route('/marketplace')
@jwt_required()
def marketplace_page():
    return render_template('marketplace.html')

@app.route('/gates')
@jwt_required()
def gates_page():
    return render_template('gates.html')

# API routes
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return jsonify({
                'status': 'error',
                'message': 'Invalid credentials'
            }), 401

        access_token = create_access_token(
            identity=username,
            additional_claims={'role': user.role}
        )

        return jsonify({
            'status': 'success',
            'token': access_token,
            'user': {
                'username': user.username,
                'role': user.role
            }
        }), 200

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Login failed'
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        # Validate input
        if not all([username, email, password]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({
                'status': 'error',
                'message': 'Username already exists'
            }), 400

        if User.query.filter_by(email=email).first():
            return jsonify({
                'status': 'error',
                'message': 'Email already registered'
            }), 400

        # Create user
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role=role,
            is_email_verified=False
        )
        db.session.add(user)
        db.session.commit()

        # Send verification email
        if email_service.send_verification_email(user):
            return jsonify({
                'status': 'success',
                'message': 'Registration successful. Please check your email to verify your account.'
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Registration successful but failed to send verification email.'
            }), 201

    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Registration failed'
        }), 500

# Protected routes that require email verification
def require_verified_email(f):
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        if not current_user.is_email_verified:
            return jsonify({
                'status': 'error',
                'message': 'Email verification required'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def require_admin():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
            return fn(*args, **kwargs)
        return wrapped
    return wrapper

# Game routes
@app.route('/api/game/profile', methods=['GET'])
@jwt_required()
@require_verified_email
def get_profile():
    try:
        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        wallet = Wallet.query.filter_by(user_id=user.id).first()
        inventory = Inventory.query.filter_by(user_id=user.id).first()

        return jsonify({
            'status': 'success',
            'profile': {
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'wallet': {
                    'address': wallet.address,
                    'balance': wallet.sol_balance,
                    'crystals': wallet.crystals,
                    'exons': wallet.exons
                },
                'inventory': {
                    'max_slots': inventory.max_slots,
                    'used_slots': len(inventory.items)
                }
            }
        }), 200
    except Exception as e:
        logging.error(f"Error getting profile: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to get profile'}), 500

# Admin routes
@app.route('/api/admin/users', methods=['GET'])
@require_admin()
def admin_list_users():
    try:
        users = User.query.all()
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_verified': user.is_email_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        return jsonify({'status': 'success', 'users': user_list}), 200
    except Exception as e:
        logging.error(f"Error listing users: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to list users'}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'Resource not found'}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    return render_template('index.html'), 500
