"""Authentication routes blueprint"""
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, g, current_app
from config import Config
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    set_access_cookies, set_refresh_cookies,
    unset_jwt_cookies, get_jwt_identity,
    jwt_required, get_jwt
)
from database import db
from models import User, Announcement
from datetime import datetime, timedelta
import bcrypt

auth_bp = Blueprint('auth', __name__)

def get_latest_announcements(limit=5):
    """Get latest active announcements"""
    try:
        return Announcement.query.filter_by(is_active=True)\
            .order_by(Announcement.priority.desc(), Announcement.created_at.desc())\
            .limit(limit)\
            .all()
    except Exception as e:
        current_app.logger.error(f"Error fetching announcements: {str(e)}")
        return []

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and form submission"""
    if request.method == 'GET':
        try:
            announcements = get_latest_announcements()
            return render_template('auth/login.html', 
                                announcements=announcements,
                                is_authenticated=current_user.is_authenticated)
        except Exception as e:
            current_app.logger.error(f"Error rendering login page: {str(e)}")
            return render_template('auth/login.html', 
                                announcements=[],
                                is_authenticated=current_user.is_authenticated)
    
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
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            current_app.logger.warning(f"Login failed - invalid password for user: {username}")
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }), 401
            flash('Invalid credentials', 'error')
            return redirect(url_for('auth.login'))

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Log in the user
        login_user(user, remember=remember)

        # Create tokens
        expires = timedelta(days=30 if remember else 1)
        access_token = create_access_token(
            identity=username,
            additional_claims={
                'role': user.role,
                'email': user.email
            },
            expires_delta=expires
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
                    'role': user.role
                }
            }), 200
        
        # Set cookies and redirect for form submission
        response = redirect(url_for('main.index'))
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

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    try:
        logout_user()
        response = redirect(url_for('main.index'))
        unset_jwt_cookies(response)
        flash('Logged out successfully', 'success')
        return response
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        flash('Logout failed', 'error')
        return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle registration page and form submission"""
    if request.method == 'GET':
        try:
            announcements = get_latest_announcements()
            return render_template('auth/register.html', 
                                announcements=announcements,
                                is_authenticated=current_user.is_authenticated)
        except Exception as e:
            current_app.logger.error(f"Error rendering register page: {str(e)}")
            return render_template('auth/register.html', 
                                announcements=[],
                                is_authenticated=current_user.is_authenticated)
    
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
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        user = User(
            username=username,
            email=email,
            password=password_hash.decode('utf-8'),
            salt=salt.decode('utf-8'),
            role='player',
            is_email_verified=True,  # Set to True for now
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
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

@auth_bp.route('/api/refresh', methods=['POST'])
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

@auth_bp.route('/api/verify', methods=['POST'])
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
