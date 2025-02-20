from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, g, current_app
from flask_jwt_extended import create_access_token, set_access_cookies, unset_access_cookies
from flask_login import login_user, logout_user, current_user
from database import db
from models import User
from datetime import datetime, timedelta
import logging

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and form submission"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.check_password(password):
            current_app.logger.warning(f"Login failed for user: {username}")
            flash('Invalid credentials', 'error')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        db.session.commit()

        current_app.logger.info(f"Login successful for user: {username}")
        return redirect(url_for('index'))

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        flash('Login failed', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/logout')
def logout():
    """Handle user logout"""
    try:
        logout_user()
        flash('Logged out successfully', 'success')
        return redirect(url_for('index'))
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
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([username, email, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))

        user = User(
            username=username,
            email=email,
            role='player',
            is_email_verified=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()

        current_app.logger.info(f"User registered successfully: {username}")
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        flash('Registration failed', 'error')
        return redirect(url_for('auth.register'))
