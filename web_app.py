from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from database import db, init_db
from models import User, PlayerCharacter, Wallet, Inventory, Transaction, Gate, Guild, Item
import os
import bcrypt
import logging
import secrets
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

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

# Ensure required static files exist
def ensure_static_directories():
    """Ensure static directories exist"""
    os.makedirs('static/images/items', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

# Initialize directories
ensure_static_directories()
os.makedirs('logs', exist_ok=True)  # Create logs directory

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

        return render_template('index.html', 
                             title='Home',
                             top_players=top_players,
                             news=news,
                             is_authenticated=get_jwt_identity() is not None)
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        logger.exception(e)  # Log full traceback
        return render_template('error.html', 
                             error_message='An error occurred while loading the page. Please try again later.'), 500

@app.route('/login')
def login_page():
    """Login page"""
    try:
        return render_template('login.html', 
                             title='Login',
                             is_authenticated=False)
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        return render_template('error.html', 
                             error_message='An error occurred while loading the page. Please try again later.'), 500

@app.route('/marketplace')
def marketplace_page():
    """Marketplace page"""
    try:
        # Create sample items if none exist
        items = [
            {
                'id': 1,
                'name': 'Legendary Sword',
                'type': 'Weapon',
                'rarity': 'Legendary',
                'image': 'items/sword.jpg',
                'stats': {
                    'Attack': '+100',
                    'Speed': '+20',
                    'Critical': '15%'
                },
                'price': 1000
            },
            {
                'id': 2,
                'name': 'Mythic Armor',
                'type': 'Armor',
                'rarity': 'Epic',
                'image': 'items/armor.jpg',
                'stats': {
                    'Defense': '+80',
                    'HP': '+500',
                    'Magic Resist': '+30'
                },
                'price': 800
            },
            {
                'id': 3,
                'name': 'Health Potion',
                'type': 'Consumable',
                'rarity': 'Common',
                'image': 'items/potion.jpg',
                'stats': {
                    'Heal': '200 HP',
                    'Duration': 'Instant',
                    'Cooldown': '30s'
                },
                'price': 50
            },
            {
                'id': 4,
                'name': 'Ring of Power',
                'type': 'Accessory',
                'rarity': 'Rare',
                'image': 'items/ring.jpg',
                'stats': {
                    'All Stats': '+15',
                    'Magic Power': '+25',
                    'MP Regen': '+10%'
                },
                'price': 500
            }
        ]

        return render_template('marketplace.html', 
                             title='Marketplace',
                             items=items,
                             is_authenticated=get_jwt_identity() is not None,
                             can_edit=get_jwt_identity() is not None)
    except Exception as e:
        logger.error(f"Error rendering marketplace page: {str(e)}")
        return render_template('error.html',
                             error_message='Failed to load marketplace. Please try again later.'), 500

@app.route('/marketplace/item', methods=['POST'])
@jwt_required()
def create_marketplace_item():
    """Create new marketplace item - requires authentication"""
    try:
        data = request.get_json()
        # Implementation for creating item
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error creating marketplace item: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/leaderboard')
def leaderboard_page():
    """Leaderboard page"""
    try:
        # Create sample hunters if none exist
        hunters = [
            {
                'user': {'username': 'Shadow Monarch'},
                'rank': 'S',
                'level': 100,
                'gates_cleared': 1234,
                'monsters_defeated': 5678
            },
            {
                'user': {'username': 'Frost Queen'},
                'rank': 'S',
                'level': 98,
                'gates_cleared': 1156,
                'monsters_defeated': 4567
            },
            {
                'user': {'username': 'Dragon Slayer'},
                'rank': 'A',
                'level': 95,
                'gates_cleared': 1089,
                'monsters_defeated': 3456
            },
            {
                'user': {'username': 'Storm Mage'},
                'rank': 'A',
                'level': 92,
                'gates_cleared': 987,
                'monsters_defeated': 2345
            },
            {
                'user': {'username': 'Blade Master'},
                'rank': 'B',
                'level': 90,
                'gates_cleared': 876,
                'monsters_defeated': 1234
            }
        ]

        # Create sample guilds if none exist
        guilds = [
            {
                'name': 'Abyss Walkers',
                'level': 50,
                'member_count': 100,
                'achievement_count': 250
            },
            {
                'name': 'Crimson Dawn',
                'level': 48,
                'member_count': 95,
                'achievement_count': 230
            },
            {
                'name': 'Shadow Legion',
                'level': 45,
                'member_count': 90,
                'achievement_count': 210
            },
            {
                'name': 'Azure Knights',
                'level': 43,
                'member_count': 85,
                'achievement_count': 190
            },
            {
                'name': 'Phoenix Guard',
                'level': 40,
                'member_count': 80,
                'achievement_count': 170
            }
        ]

        return render_template('leaderboard.html', 
                             title='Leaderboard',
                             hunters=hunters,
                             guilds=guilds,
                             is_authenticated=get_jwt_identity() is not None)
    except Exception as e:
        logger.error(f"Error rendering leaderboard page: {str(e)}")
        return render_template('error.html',
                             error_message='Failed to load leaderboard. Please try again later.'), 500

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
            },
            'redirect_url': 'https://play.terminusa.online',
            'message': 'Login successful! Redirecting to game...'
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

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)

        # Create user
        user = User(
            username=username,
            email=email,
            password=password_hash.decode('utf-8'),
            salt=salt.decode('utf-8'),
            role='player',
            is_email_verified=False,
            email_verification_token=verification_token,
            email_verification_sent_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.flush()

        # Create character and other user data
        character = PlayerCharacter(user_id=user.id)
        wallet = Wallet(user_id=user.id)
        inventory = Inventory(user_id=user.id)
        
        db.session.add_all([character, wallet, inventory])
        db.session.commit()

        # Send verification email
        verification_url = f"https://terminusa.online/verify_email/{verification_token}"
        send_verification_email(email, username, verification_url)

        return jsonify({
            'status': 'success',
            'message': 'Registration successful! Please check your email to verify your account.'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Registration failed'}), 500

def send_verification_email(email, username, verification_url):
    """Send verification email"""
    try:
        subject = "Verify your Terminusa Online account"
        body = f"""
        Welcome to Terminusa Online, {username}!

        Please click the link below to verify your email address:
        {verification_url}

        This link will expire in 24 hours.

        If you did not create an account, please ignore this email.

        Best regards,
        The Terminusa Online Team
        """

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = os.getenv('SMTP_USER')
        msg['To'] = email

        with smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT'))) as server:
            server.starttls()
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
            server.send_message(msg)

        logger.info(f"Verification email sent to {email}")
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        raise

@app.route('/verify_email/<token>')
def verify_email(token):
    """Handle email verification"""
    try:
        user = User.query.filter_by(email_verification_token=token).first()
        if not user:
            return render_template('error.html',
                                 error_message='Invalid verification token.'), 400

        # Check if token is expired (24 hours)
        if (datetime.utcnow() - user.email_verification_sent_at).total_seconds() > 86400:
            return render_template('error.html',
                                 error_message='Verification token has expired.'), 400

        user.is_email_verified = True
        user.email_verification_token = None
        db.session.commit()

        return render_template('message.html',
                             title='Email Verified',
                             message='Your email has been verified successfully. You can now log in.')

    except Exception as e:
        logger.error(f"Error verifying email: {str(e)}")
        return render_template('error.html',
                             error_message='An error occurred during email verification.'), 500

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
    # Get port from environment or use default
    port = int(os.getenv('WEBAPP_PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug)
