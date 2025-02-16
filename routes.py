from flask import jsonify, request, render_template
from app import app, db
from models import User, Transaction, ChatMessage
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from email_service import email_service

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

@app.route('/api/protected-resource', methods=['GET'])
@require_verified_email
def protected_resource():
    return jsonify({
        'status': 'success',
        'message': 'Access granted to protected resource'
    }), 200

# [Previous routes remain the same...]
