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
app = Flask(__name__, 
            static_url_path='/static',
            static_folder='static')
CORS(app)

# Ensure static directory exists
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# Configure app
app.config.update(
    SEND_FILE_MAX_AGE_DEFAULT=0,  # Disable caching during development
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'dev-key-please-change'),
    JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'jwt-key-please-change'),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
)

# Initialize extensions
jwt = JWTManager(app)
init_db(app)

# Ensure required static files exist
def ensure_static_files():
    """Ensure required static files exist"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    images_dir = os.path.join(static_dir, 'images')
    
    # Create directories if they don't exist
    os.makedirs(images_dir, exist_ok=True)
    
    # Create placeholder images if they don't exist
    for i in range(1, 4):
        image_path = os.path.join(images_dir, f'news{i}.jpg')
        if not os.path.exists(image_path):
            # Create a simple colored rectangle as placeholder
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 400), color='purple')
            d = ImageDraw.Draw(img)
            d.text((400, 200), f'News {i}', fill='white', anchor='mm')
            img.save(image_path)

# Initialize static files
ensure_static_files()

@app.route('/')
def index():
    """Main landing page"""
    try:
        # Get top players for the leaderboard section
        top_players = PlayerCharacter.query.order_by(
            PlayerCharacter.level.desc(),
            PlayerCharacter.gates_cleared.desc()
        ).limit(3).all()

        if not top_players:
            # Add placeholder data if no players exist
            top_players = [
                {'user': {'username': 'Shadow Monarch'}, 'level': 100, 'gates_cleared': 1234, 'rank': 'S'},
                {'user': {'username': 'Frost Queen'}, 'level': 98, 'gates_cleared': 1156, 'rank': 'S'},
                {'user': {'username': 'Dragon Slayer'}, 'level': 95, 'gates_cleared': 1089, 'rank': 'S'}
            ]

        # Get latest news
        news = [
            {
                'date': '2025-02-17',
                'title': 'New Gate System Released',
                'content': 'Experience the thrill of our new gate system. Challenge powerful monsters and earn legendary rewards.',
                'image': 'news1.jpg'
            },
            {
                'date': '2025-02-16',
                'title': 'Season 1 Rankings',
                'content': 'The first season rankings are in! See who made it to the top of the hunter rankings.',
                'image': 'news2.jpg'
            },
            {
                'date': '2025-02-15',
                'title': 'New Magic Beasts Discovered',
                'content': 'Mysterious new magic beasts have appeared in the gates. Can you defeat them?',
                'image': 'news3.jpg'
            }
        ]

        return render_template('index_new.html', 
                             title='Home',
                             top_players=top_players,
                             news=news)
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        logger.exception(e)  # Log full traceback
        return render_template('error.html', 
                             error_message='An error occurred while loading the page. Please try again later.'), 500

@app.route('/gates')
@jwt_required()
def gates_page():
    """Gates page"""
    try:
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        available_gates = Gate.query.all()
        return render_template('gates.html', 
                             title='Gates',
                             user=current_user,
                             available_gates=available_gates)
    except Exception as e:
        logger.error(f"Error rendering gates page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

@app.route('/gates/<int:gate_id>/enter', methods=['POST'])
@jwt_required()
def enter_gate(gate_id):
    """Enter a gate"""
    try:
        gate = Gate.query.get_or_404(gate_id)
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
        
        # Check if user meets requirements
        if current_user.level < gate.min_level:
            return jsonify({
                'status': 'error',
                'message': f'Required level: {gate.min_level}'
            }), 400
        
        return jsonify({
            'status': 'success',
            'gate_state': {
                'id': gate.id,
                'name': gate.name,
                'grade': gate.grade,
                'party': [{
                    'username': current_user.username,
                    'hp': 100,
                    'max_hp': 100
                }]
            }
        })
    except Exception as e:
        logger.error(f"Error entering gate: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to enter gate'}), 500

@app.route('/gates/<int:gate_id>/exit', methods=['POST'])
@jwt_required()
def exit_gate(gate_id):
    """Exit a gate"""
    try:
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error exiting gate: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to exit gate'}), 500

@app.route('/party/create', methods=['POST'])
@jwt_required()
def create_party():
    """Create a new party"""
    try:
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error creating party: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to create party'}), 500

@app.route('/party/list', methods=['GET'])
@jwt_required()
def list_parties():
    """List available parties"""
    try:
        return jsonify({
            'status': 'success',
            'parties': []
        })
    except Exception as e:
        logger.error(f"Error listing parties: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to list parties'}), 500

@app.route('/party/invite', methods=['POST'])
@jwt_required()
def invite_to_party():
    """Invite a player to party"""
    try:
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error inviting to party: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to send invitation'}), 500

@app.route('/party/leave', methods=['POST'])
@jwt_required()
def leave_party():
    """Leave current party"""
    try:
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error leaving party: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to leave party'}), 500

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
        return render_template('login.html', title='Login')
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

@app.route('/register')
def register_page():
    """Registration page"""
    try:
        return render_template('register.html', title='Register')
    except Exception as e:
        logger.error(f"Error rendering register page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

@app.route('/play')
@jwt_required()
def play_page():
    """Game page"""
    try:
        return render_template('play.html', title='Play')
    except Exception as e:
        logger.error(f"Error rendering play page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to render page'}), 500

@app.route('/marketplace')
@jwt_required()
def marketplace_page():
    """Marketplace page"""
    try:
        return render_template('marketplace.html', title='Marketplace')
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
        return render_template('leaderboard.html', title='Leaderboard', players=top_players)
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
    return render_template('error.html', 
                         error_message='The page you are looking for could not be found.'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', 
                         error_message='An internal server error occurred. Please try again later.'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions"""
    logger.exception(error)  # Log full traceback
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': str(error)}), 500
    return render_template('error.html', 
                         error_message='An unexpected error occurred. Please try again later.'), 500

if __name__ == '__main__':
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.getenv('WEBAPP_PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug)
