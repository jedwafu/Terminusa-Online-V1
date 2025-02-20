from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, g
from flask_jwt_extended import create_access_token, set_access_cookies, unset_access_cookies
from database import db
from models import User

auth = Blueprint('auth', __name__)
from datetime import datetime, timedelta
import bcrypt
import logging

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and form submission"""
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
            return redirect(url_for('login'))

        # Try to find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            app.logger.warning(f"Login failed - user not found: {username}")
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }), 401
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            app.logger.warning(f"Login failed - invalid password for user: {username}")
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }), 401
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Create access token
        expires = timedelta(days=30 if remember else 1)
        access_token = create_access_token(
            identity=username,
            additional_claims={'role': user.role},
            expires_delta=expires
        )

        app.logger.info(f"Login successful for user: {username}")
        
        if request.is_json:
            return jsonify({
                'status': 'success',
                'token': access_token,
                'user': {
                    'username': user.username,
                    'role': user.role
                },
                'redirect': url_for('play')
            }), 200
        
        # Set cookie and redirect for form submission
        response = redirect(url_for('play'))
        set_access_cookies(response, access_token)
        flash('Login successful!', 'success')
        return response

    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        if request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Login failed'
            }), 500
        flash('Login failed', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Handle user logout"""
    try:
        response = redirect(url_for('index'))
        unset_access_cookies(response)
        flash('Logged out successfully', 'success')
        return response
    except Exception as e:
        app.logger.error(f"Logout error: {str(e)}")
        flash('Logout failed', 'error')
        return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle registration page and form submission"""
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
            return redirect(url_for('register'))

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Username already exists'
                }), 400
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Email already registered'
                }), 400
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

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

        app.logger.info(f"User registered successfully: {username}")
        
        if request.is_json:
            return jsonify({
                'status': 'success',
                'message': 'Registration successful! You can now log in.'
            }), 201
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        if request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Registration failed'
            }), 500
        flash('Registration failed', 'error')
        return redirect(url_for('register'))
