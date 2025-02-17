from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from database import db, init_db
from models import User, PlayerCharacter, Wallet, Inventory, Transaction, Gate
import os
import bcrypt
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure app
app.config.update(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'dev-key-please-change'),
    JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'jwt-key-please-change'),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
)

# Initialize extensions
jwt = JWTManager(app)
init_db(app)

@app.route('/')
def index():
    """Main landing page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/login')
def login_page():
    """Login page"""
    try:
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

@app.route('/register')
def register_page():
    """Registration page"""
    try:
        return render_template('register.html')
    except Exception as e:
        logger.error(f"Error rendering register page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

@app.route('/play')
def play_page():
    """Game page"""
    try:
        return render_template('play.html')
    except Exception as e:
        logger.error(f"Error rendering play page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

@app.route('/marketplace')
def marketplace_page():
    """Marketplace page"""
    try:
        return render_template('marketplace.html')
    except Exception as e:
        logger.error(f"Error rendering marketplace page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

@app.route('/leaderboard')
def leaderboard_page():
    """Leaderboard page"""
    try:
        top_players = PlayerCharacter.query.order_by(
            PlayerCharacter.level.desc(),
            PlayerCharacter.gates_cleared.desc()
        ).limit(100).all()
        return render_template('leaderboard.html', players=top_players)
    except Exception as e:
        logger.error(f"Error rendering leaderboard page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

# API Routes
@app.route('/api/login', methods=['POST'])
def login():
    """Handle login requests"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'status': 'error', 'message': 'Missing credentials'}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

        # Update last login
        user.last_login = db.func.now()
        db.session.commit()

        # Create access token
        access_token = create_access_token(identity=username)

        return jsonify({
            'status': 'success',
            'token': access_token,
            'user': {
                'username': user.username,
                'role': user.role
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Login failed'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Handle registration requests"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        # Check if user exists
        if User.query.filter_by(username=username).first():
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'status': 'error', 'message': 'Email already registered'}), 400

        # Create password hash
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

        # Create user
        user = User(
            username=username,
            email=email,
            password=password_hash.decode('utf-8'),
            salt=salt.decode('utf-8'),
            role='player',
            is_email_verified=True  # TODO: Implement email verification
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

        # Create wallet
        wallet = Wallet(
            user_id=user.id,
            address=f"wallet_{os.urandom(8).hex()}",
            encrypted_privkey=os.urandom(32).hex(),
            iv=os.urandom(16).hex(),
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

        return jsonify({
            'status': 'success',
            'message': 'Registration successful! You can now log in.'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Registration failed'}), 500

@app.route('/api/marketplace/items', methods=['GET'])
@jwt_required()
def get_marketplace_items():
    """Get marketplace items"""
    try:
        # TODO: Implement marketplace items
        return jsonify({'items': []})
    except Exception as e:
        logger.error(f"Error getting marketplace items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard data"""
    try:
        top_players = PlayerCharacter.query.order_by(
            PlayerCharacter.level.desc(),
            PlayerCharacter.gates_cleared.desc()
        ).limit(100).all()

        return jsonify({
            'players': [{
                'username': player.user.username,
                'level': player.level,
                'rank': player.rank,
                'gates_cleared': player.gates_cleared
            } for player in top_players]
        })
    except Exception as e:
        logger.error(f"Error getting leaderboard data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('index.html'), 500

if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.getenv('WEBAPP_PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug)
