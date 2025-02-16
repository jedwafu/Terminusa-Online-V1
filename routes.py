from flask import jsonify, request, render_template, send_from_directory, make_response, redirect
from app import app, db
from models import (
    User, PlayerCharacter, PlayerSkill, Wallet, Item, 
    Inventory, InventoryItem, Guild, GuildMember, Party, 
    PartyMember, PartyInvitation, Gate, GateSession, 
    MagicBeast, Achievement, AIBehavior, Transaction, 
    ChatMessage
)
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request, create_access_token
import logging
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from email_service import email_service
import os
from functools import wraps
import secrets

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
def play_redirect():
    return redirect('https://play.terminusa.online', code=301)

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
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400

        app.logger.info(f"Login attempt for user: {username}")
        user = db.session.query(User).filter_by(username=username).first()
        
        if not user:
            app.logger.warning(f"Login failed - user not found: {username}")
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

        if not check_password_hash(user.password, password):
            app.logger.warning(f"Login failed - invalid password for user: {username}")
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        access_token = create_access_token(
            identity=username,
            additional_claims={'role': user.role}
        )

        app.logger.info(f"Login successful for user: {username}")
        return jsonify({
            'status': 'success',
            'token': access_token,
            'user': {
                'username': user.username,
                'role': user.role
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Login failed'
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Validate input
        if not all([username, email, password]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400

        # Check if user already exists
        if db.session.query(User).filter_by(username=username).first():
            return jsonify({
                'status': 'error',
                'message': 'Username already exists'
            }), 400

        if db.session.query(User).filter_by(email=email).first():
            return jsonify({
                'status': 'error',
                'message': 'Email already registered'
            }), 400

        # Create user
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='player',
            is_email_verified=False,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.flush()  # Get user.id

        # Create character
        character = PlayerCharacter(
            user_id=user.id,
            level=1,
            experience=0,
            rank='F',
            title='Novice Hunter'
        )
        db.session.add(character)

        # Create wallet with starting values
        wallet = Wallet(
            user_id=user.id,
            address=f"wallet_{secrets.token_hex(8)}",
            encrypted_privkey=secrets.token_hex(32),
            iv=secrets.token_hex(16),
            sol_balance=0.0,
            crystals=int(os.getenv('STARTING_CRYSTALS', 20)),
            exons=int(os.getenv('STARTING_EXONS', 0))
        )
        db.session.add(wallet)

        # Create inventory
        inventory = Inventory(
            user_id=user.id,
            max_slots=int(os.getenv('STARTING_INVENTORY_SLOTS', 20))
        )
        db.session.add(inventory)

        db.session.commit()

        app.logger.info(f"User registered successfully: {username}")

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
        app.logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Registration failed'
        }), 500

@app.route('/api/game/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        username = get_jwt_identity()
        user = db.session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        character = user.character
        wallet = user.wallet
        inventory = user.inventory

        return jsonify({
            'status': 'success',
            'character': {
                'level': character.level,
                'experience': character.experience,
                'rank': character.rank,
                'title': character.title,
                'strength': character.strength,
                'agility': character.agility,
                'intelligence': character.intelligence,
                'vitality': character.vitality,
                'wisdom': character.wisdom,
                'hp': character.hp,
                'mp': character.mp,
                'physical_attack': character.physical_attack,
                'magical_attack': character.magical_attack,
                'physical_defense': character.physical_defense,
                'magical_defense': character.magical_defense,
                'critical_chance': character.critical_chance,
                'critical_damage': character.critical_damage,
                'dodge_chance': character.dodge_chance,
                'hit_chance': character.hit_chance,
                'gates_cleared': character.gates_cleared,
                'bosses_defeated': character.bosses_defeated,
                'quests_completed': character.quests_completed
            },
            'wallet': {
                'crystals': wallet.crystals,
                'exons': wallet.exons
            },
            'inventory': {
                'max_slots': inventory.max_slots,
                'used_slots': len(inventory.items)
            }
        }), 200
    except Exception as e:
        app.logger.error(f"Error getting profile: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to get profile'}), 500

@app.route('/api/game/gates', methods=['GET'])
@jwt_required()
def list_gates():
    try:
        username = get_jwt_identity()
        user = db.session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        character = user.character
        gates = db.session.query(Gate).filter(
            Gate.level_requirement <= character.level
        ).all()

        return jsonify({
            'status': 'success',
            'gates': [{
                'id': gate.id,
                'name': gate.name,
                'description': gate.description,
                'type': gate.type.value,
                'level_requirement': gate.level_requirement,
                'rank_requirement': gate.rank_requirement,
                'min_players': gate.min_players,
                'max_players': gate.max_players,
                'rewards': gate.rewards
            } for gate in gates]
        }), 200
    except Exception as e:
        app.logger.error(f"Error listing gates: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to list gates'}), 500

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
