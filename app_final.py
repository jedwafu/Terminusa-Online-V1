from gevent import monkey
monkey.patch_all()

import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, current_user, login_required
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from functools import wraps

from database import db
from models import User, Announcement
from routes.auth_routes import auth

# Load environment variables
print("[DEBUG] Loading environment variables")
load_dotenv(override=True)

# Validate required environment variables
required_env_vars = [
    'FLASK_SECRET_KEY',
    'JWT_SECRET_KEY',
    'DATABASE_URL',
    'SERVER_PORT',
    'WEBAPP_PORT'
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {missing_vars}")

# Initialize Flask app
print("[DEBUG] Creating Flask app")
app = Flask(__name__)

# Configure app
print("[DEBUG] Configuring Flask app")
app.config.update(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY'),
    JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY'),
    JWT_ACCESS_TOKEN_EXPIRES=3600,  # 1 hour
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    CORS_HEADERS='Content-Type',
    SEND_FILE_MAX_AGE_DEFAULT=31536000,  # 1 year in seconds
    STATIC_FOLDER=os.path.abspath('static')
)

# Initialize extensions
print("[DEBUG] Initializing extensions")
jwt = JWTManager(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Initialize database
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler(
    'logs/terminusa.log',
    maxBytes=1024 * 1024,  # 1MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
app.logger.info('Terminusa Online startup')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Register blueprints
app.register_blueprint(auth, url_prefix='/auth')

# Routes
@app.route('/')
def index():
    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.priority.desc(), Announcement.created_at.desc())\
        .limit(3)\
        .all()
    return render_template('index.html', announcements=announcements)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/api/connect-wallet', methods=['POST'])
@login_required
def connect_wallet():
    data = request.get_json()
    wallet_address = data.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'error': 'Wallet address is required'}), 400
    
    current_user.web3_wallet = wallet_address
    db.session.commit()
    
    return jsonify({
        'message': 'Wallet connected successfully',
        'wallet_address': wallet_address
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Page not found: {error}')
    return render_template('error.html',
                         error_message='The page you are looking for could not be found.',
                         title='404 Not Found'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server error: {error}')
    db.session.rollback()
    return render_template('error.html',
                         error_message='An internal server error occurred. Please try again later.',
                         title='500 Server Error'), 500

if __name__ == '__main__':
    port = int(os.getenv('SERVER_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Use gevent WSGI server
    from gevent.pywsgi import WSGIServer
    http_server = WSGIServer(('0.0.0.0', port), app)
    http_server.serve_forever()
