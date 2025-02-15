import datetime
from flask import request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
import base58
import hashlib
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from Crypto.Util.Padding import pad, unpad
import os
from functools import wraps

from app import app, SOLANA_RPC_URL
from db_setup import db
from models import User, Wallet, Inventory, InventoryItem, Item, Gate, MagicBeast, Guild, GuildMember, Achievement, AIBehavior, Party, PartyMember, PartyInvitation, GateSession

def require_admin():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            print(f"[DEBUG] JWT claims: {claims}")  # Debug JWT claims
            if claims.get('role') != 'admin':
                print(f"[DEBUG] Access denied. User role: {claims.get('role')}")
                return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
            return fn(*args, **kwargs)
        return wrapped
    return wrapper

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
        
        print(f"[DEBUG] User found - ID: {user.id}, Role: {user.role}")  # Debug user details
        
        if not check_password_hash(user.password, data.get('password', '')):
            print("[DEBUG] Password does not match")
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

        wallet = Wallet.query.filter_by(user_id=user.id).first()
        if not wallet:
            print("[DEBUG] Wallet not found")
            return jsonify({'status': 'error', 'message': 'Wallet not found'}), 404

        # Create JWT with role claim
        additional_claims = {'role': user.role}
        print(f"[DEBUG] Creating JWT with claims: {additional_claims}")  # Debug JWT creation
        
        access_token = create_access_token(
            identity=user.username,
            additional_claims=additional_claims,
            expires_delta=datetime.timedelta(minutes=15)
        )
        
        response_data = {
            'status': 'success',
            'token': access_token,
            'role': user.role,  # Include role in response
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,  # Include role in user data
            },
            'wallet': {
                'address': wallet.address,
                'balance': wallet.sol_balance,
                'assets': {'crystals': wallet.crystals, 'exons': wallet.exons}
            }
        }
        print(f"[DEBUG] Login response data: {response_data}")  # Debug response
        return jsonify(response_data), 200

    except Exception as e:
        print(f"[DEBUG] Exception occurred: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Login failed'}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    try:
        username = data.get('username', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'user').lower()
        
        print(f"[DEBUG] Registration attempt - Username: {username}, Role: {role}")  # Debug registration
        
        if not (6 <= len(username) <= 20):
            return jsonify({'status': 'error', 'message': 'Username must be 6-20 characters'}), 400
        if len(password) < 8:
            return jsonify({'status': 'error', 'message': 'Password must be ≥8 characters'}), 400
        if role not in ['user', 'admin']:
            return jsonify({'status': 'error', 'message': 'Invalid role'}), 400

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 400

        salt = os.urandom(16).hex()
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            salt=salt,
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"[DEBUG] User created - ID: {new_user.id}, Role: {new_user.role}")  # Debug user creation

        try:
            keypair = Keypair()
            key_material = generate_key_material(username)
            derived_key = PBKDF2(key_material, bytes.fromhex(salt), 32, 100000)
            cipher = AES.new(derived_key, AES.MODE_CBC)
            secret_bytes = keypair.secret()
            encrypted_key = cipher.encrypt(pad(secret_bytes, AES.block_size))
            
            new_wallet = Wallet(
                user_id=new_user.id,
                address=str(keypair.pubkey()),
                encrypted_privkey=base58.b58encode(encrypted_key).decode(),
                iv=base58.b58encode(cipher.iv).decode()
            )
            
            db.session.add(new_wallet)
            db.session.commit()
            print("[DEBUG] Wallet created successfully")  # Debug wallet creation
        except Exception as e:
            print(f"[DEBUG] Wallet creation failed: {str(e)}")  # Debug wallet error
            try:
                db.session.delete(new_user)
                db.session.commit()
            except Exception:
                db.session.rollback()
            raise Exception("Failed to create wallet")

        return jsonify({'status': 'success', 'message': 'User created'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e) if str(e) != "Failed to create wallet" else 'Registration failed'}), 500

# ======== ADMIN ROUTES ========
@app.route('/admin/users', methods=['GET'])
@jwt_required()
def admin_list_users():
    try:
        # Verify admin role
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

        print("[DEBUG] Admin attempting to list users")  # Debug admin access
        users = User.query.all()
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        print(f"[DEBUG] Found {len(user_list)} users")  # Debug user count
        return jsonify({'status': 'success', 'users': user_list}), 200
    except Exception as e:
        print(f"[DEBUG] Error listing users: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to list users'}), 500

@app.route('/admin/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def admin_update_user(user_id):
    try:
        # Verify admin role
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

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
@jwt_required()
def admin_delete_user(user_id):
    try:
        # Verify admin role
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Failed to delete user'}), 500

@app.route('/admin/wallets', methods=['GET'])
@jwt_required()
def admin_list_wallets():
    try:
        # Verify admin role
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

        print("[DEBUG] Admin attempting to list wallets")  # Debug admin access
        wallets = Wallet.query.all()
        wallet_list = []
        for wallet in wallets:
            wallet_list.append({
                'user_id': wallet.user_id,
                'address': wallet.address,
                'sol_balance': wallet.sol_balance,
                'crystals': wallet.crystals,
                'exons': wallet.exons
            })
        print(f"[DEBUG] Found {len(wallet_list)} wallets")  # Debug wallet count
        return jsonify({'status': 'success', 'wallets': wallet_list}), 200
    except Exception as e:
        print(f"[DEBUG] Error listing wallets: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to list wallets'}), 500

# ======== HELPER FUNCTIONS ========
def generate_key_material(username):
    first_hash = hashlib.sha256(username.encode()).hexdigest()
    combined = f"{username}|{first_hash}"
    final_hash = hashlib.sha256(combined.encode()).hexdigest()
    return final_hash

# ======== ERROR HANDLING ========
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Critical error: {str(e)}", exc_info=True)
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error_type': type(e).__name__
    }), 500
