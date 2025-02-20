from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, g, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    set_access_cookies, set_refresh_cookies,
    unset_jwt_cookies, get_jwt_identity,
    jwt_required, get_jwt
)
from flask_login import login_user, logout_user, current_user, login_required
from database import db
from models import User
from datetime import datetime, timedelta
import logging
import bcrypt

auth = Blueprint('auth', __name__)

# Web Routes
@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and form submission"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        # Handle AJAX request
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            remember = data.get('remember', False)
        # Handle form submission
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember', False)

        if not username or not password:
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Username and password are required'
                }), 400
            flash('Username and password are required', 'error')
            return redirect(url_for('auth.login'))

        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            current_app.logger.warning(f"Login failed - user not found: {username}")
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }), 401
            flash('Invalid credentials', 'error')
            return redirect(url_for('auth.login'))

        # Verify password
        if not user.check_password(password):
            current_app.logger.warning(f"Login failed - invalid password for user: {username}")
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }), 401
            flash('Invalid credentials', 'error')
            return redirect(url_for('auth.login'))

        # Log in user
        login_user(user, remember=remember)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Create tokens
        access_token = create_access_token(
            identity=username,
            additional_claims={
                'role': user.role,
                'email': user.email
            },
            expires_delta=timedelta(days=30 if remember else 1)
        )
        refresh_token = create_refresh_token(
            identity=username,
            additional_claims={
                'role': user.role,
                'email': user.email
            }
        )

        current_app.logger.info(f"Login successful for user: {username}")
        
        if request.is_json:
            return jsonify({
                'status': 'success',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            }), 200
        
        # Set cookies and redirect for form submission
        response = redirect(url_for('index'))
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        flash('Login successful!', 'success')
        return response

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        if request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Login failed'
            }), 500
        flash('Login failed', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/logout')
def logout():
    """Handle user logout"""
    try:
        # Flask-Login logout
        logout_user()
        
        # Clear JWT cookies
        response = redirect(url_for('index'))
        unset_jwt_cookies(response)
        flash('Logged out successfully', 'success')
        return response
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        flash('Logout failed', 'error')
        return redirect(url_for('index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle registration page and form submission"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        # Handle AJAX request
        if request.is_json:
            data = request.get_json()
        # Handle form submission
        else:
            data = request.form

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Validate input
        if not all([username, email, password]):
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields'
                }), 400
            flash('All fields are required', 'error')
            return redirect(url_for('auth.register'))

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Username already exists'
                }), 400
            flash('Username already exists', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Email already registered'
                }), 400
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))

        # Create user
        user = User(
            username=username,
            email=email,
            role='player',
            is_email_verified=True,  # Set to True for now
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()

        current_app.logger.info(f"User registered successfully: {username}")
        
        if request.is_json:
            return jsonify({
                'status': 'success',
                'message': 'Registration successful! You can now log in.'
            }), 201
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        if request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Registration failed'
            }), 500
        flash('Registration failed', 'error')
        return redirect(url_for('auth.register'))

# API Routes
@auth.route('/api/login', methods=['POST'])
def api_login():
    """Handle API login requests"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        remember = data.get('remember', False)

        if not username or not password:
            return jsonify({
                'status': 'error',
                'message': 'Username and password are required'
            }), 400

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user or not user.check_password(password):
            return jsonify({
                'status': 'error',
                'message': 'Invalid credentials'
            }), 401

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Create tokens
        access_token = create_access_token(
            identity=username,
            additional_claims={
                'role': user.role,
                'email': user.email
            },
            expires_delta=timedelta(days=30 if remember else 1)
        )
        refresh_token = create_refresh_token(
            identity=username,
            additional_claims={
                'role': user.role,
                'email': user.email
            }
        )

        return jsonify({
            'status': 'success',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"API login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Login failed'
        }), 500

@auth.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        access_token = create_access_token(
            identity=identity,
            additional_claims={
                'role': claims.get('role'),
                'email': claims.get('email')
            }
        )
        
        return jsonify({
            'status': 'success',
            'access_token': access_token
        }), 200
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Token refresh failed'
        }), 500

@auth.route('/api/verify-token', methods=['POST'])
@jwt_required()
def verify_token():
    """Verify access token"""
    try:
        identity = get_jwt_identity()
        claims = get_jwt()
        
        return jsonify({
            'status': 'success',
            'user': {
                'username': identity,
                'role': claims.get('role'),
                'email': claims.get('email')
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Token verification error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Token verification failed'
        }), 500

@auth.route('/api/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({
                'status': 'error',
                'message': 'Current and new passwords are required'
            }), 400

        username = get_jwt_identity()
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(current_password):
            return jsonify({
                'status': 'error',
                'message': 'Current password is incorrect'
            }), 401

        user.set_password(new_password)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Password changed successfully'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Password change error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Password change failed'
        }), 500

# Error handlers
@auth.errorhandler(401)
def unauthorized(error):
    if request.is_json:
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized'
        }), 401
    flash('Please log in to access this page', 'error')
    return redirect(url_for('auth.login'))

@auth.errorhandler(403)
def forbidden(error):
    if request.is_json:
        return jsonify({
            'status': 'error',
            'message': 'Forbidden'
        }), 403
    flash('You do not have permission to access this page', 'error')
    return redirect(url_for('index'))
