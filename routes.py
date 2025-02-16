from flask import jsonify, request, render_template
from app import app, db
from models import User, Transaction, ChatMessage, Wallet, Inventory, Item, Gate, Guild
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from email_service import email_service
from functools import wraps
import os
import secrets

# Health check route
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

# Authentication routes
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    
    try:
        print(f"[DEBUG] Attempting to log in user: {username}")
        user = User.query.filter_by(username=username).first()
        if not user:
            print("[DEBUG] User not found")
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
        
        if not check_password_hash(user.password, data.get('password', '')):
            print("[DEBUG] Password does not match")
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

        wallet = Wallet.query.filter_by(user_id=user.id).first()
        if not wallet:
            print("[DEBUG] Wallet not found")
            return jsonify({'status': 'error', 'message': 'Wallet not found'}), 404

        # Create JWT with role claim
        additional_claims = {'role': user.role}
        access_token = create_access_token(
            identity=user.username,
            additional_claims=additional_claims,
            expires_delta=timedelta(minutes=15)
        )
        
        response_data = {
            'status': 'success',
            'token': access_token,
            'role': user.role,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
            },
            'wallet': {
                'address': wallet.address,
                'balance': wallet.sol_balance,
                'assets': {'crystals': wallet.crystals, 'exons': wallet.exons}
            }
        }
        return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Login failed'}), 500

@app.route('/register', methods=['POST'])
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
            is_email_verified=False,
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.flush()  # Get user.id

        # Create wallet
        wallet = Wallet(
            user_id=user.id,
            address=f"wallet_{secrets.token_hex(8)}",
            encrypted_privkey=f"key_{secrets.token_hex(16)}",
            iv=f"iv_{secrets.token_hex(8)}",
            sol_balance=0.0,
            crystals=100,  # Starting crystals
            exons=10      # Starting exons
        )
        db.session.add(wallet)

        # Create inventory
        inventory = Inventory(
            user_id=user.id,
            max_slots=100  # Starting inventory size
        )
        db.session.add(inventory)

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

@app.route('/verify-email', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    if not token:
        return jsonify({
            'status': 'error',
            'message': 'Verification token is required'
        }), 400

    user = User.query.filter_by(email_verification_token=token).first()
    if not user:
        return jsonify({
            'status': 'error',
            'message': 'Invalid verification token'
        }), 400

    if user.email_verification_sent_at + timedelta(hours=24) < datetime.utcnow():
        return jsonify({
            'status': 'error',
            'message': 'Verification token has expired'
        }), 400

    user.is_email_verified = True
    user.email_verification_token = None
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Email verified successfully'
    }), 200

@app.route('/resend-verification', methods=['POST'])
def resend_verification():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'status': 'error',
                'message': 'Email is required'
            }), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404

        if user.is_email_verified:
            return jsonify({
                'status': 'error',
                'message': 'Email is already verified'
            }), 400

        # Check if we should wait before sending another email
        if user.email_verification_sent_at:
            time_since_last = datetime.utcnow() - user.email_verification_sent_at
            if time_since_last < timedelta(minutes=5):
                return jsonify({
                    'status': 'error',
                    'message': 'Please wait 5 minutes before requesting another verification email'
                }), 429

        if email_service.send_verification_email(user):
            return jsonify({
                'status': 'success',
                'message': 'Verification email sent'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send verification email'
            }), 500

    except Exception as e:
        logging.error(f"Resend verification error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to resend verification email'
        }), 500

@app.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'status': 'error',
                'message': 'Email is required'
            }), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal that the email doesn't exist
            return jsonify({
                'status': 'success',
                'message': 'If your email is registered, you will receive a password reset link'
            }), 200

        if email_service.send_password_reset_email(user):
            return jsonify({
                'status': 'success',
                'message': 'Password reset email sent'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send password reset email'
            }), 500

    except Exception as e:
        logging.error(f"Password reset request error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to process password reset request'
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

# Admin routes
@app.route('/admin/users', methods=['GET'])
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

@app.route('/admin/users/<int:user_id>', methods=['PUT'])
@require_admin()
def admin_update_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        data = request.json
        if 'username' in data:
            user.username = data['username']
        if 'password' in data:
            user.password = generate_password_hash(data['password'])
        if 'role' in data:
            user.role = data['role']

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Failed to update user'}), 500

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@require_admin()
def admin_delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Failed to delete user'}), 500

# Game routes
@app.route('/game/profile', methods=['GET'])
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

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'status': 'error', 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
