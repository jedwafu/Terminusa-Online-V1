from flask import jsonify, request, render_template, send_from_directory, make_response
from app import app, db
from models import User, Transaction, ChatMessage, Wallet, Inventory, Item, Gate, Guild
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
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

# Authentication routes
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
