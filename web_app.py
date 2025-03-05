import os
from gevent import monkey
monkey.patch_all()
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from dotenv import load_dotenv
from database import db
from models import User, PlayerCharacter, Wallet, Inventory, Transaction, Gate, Guild, Item, Announcement
from routes.pages import pages_bp
import bcrypt
import logging
import secrets
from datetime import datetime
import smtplib
import email.utils
from email.mime.text import MIMEText

def create_app():
    """Create and configure the Flask application"""
    # Create required directories
    os.makedirs('static/images/items', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    app = Flask(__name__, 
                static_url_path='/static',
                static_folder='static')
    CORS(app)

    # Load environment variables
    load_dotenv()

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
    db.init_app(app)

    return app

app = create_app()

# Register blueprints
app.register_blueprint(pages_bp)

# Configure logging
os.makedirs('logs', exist_ok=True)  # Ensure logs directory exists
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create file handler
file_handler = logging.FileHandler('logs/web.log')
file_handler.setFormatter(formatter)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Also configure root logger to ensure all logs are captured
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

@app.route('/play')
def play_page():
    """Play page"""
    return redirect('https://play.terminusa.online')

@app.route('/login')
def login_page():
    """Login page"""
    try:
        return render_template('login_new.html', 
                             title='Login',
                             is_authenticated=False)
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        return render_template('error.html', 
                             error_message='An error occurred while loading the page. Please try again later.'), 500

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

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('WEBAPP_PORT', 3000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Run the app
    from gevent.pywsgi import WSGIServer
    http_server = WSGIServer(('0.0.0.0', port), app)
    http_server.serve_forever()
