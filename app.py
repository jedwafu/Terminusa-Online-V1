from gevent import monkey
monkey.patch_all()

import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from database import db, init_db

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
    CORS_HEADERS='Content-Type'
)

# Initialize extensions
print("[DEBUG] Initializing extensions")
jwt = JWTManager(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for API routes

# Initialize database
init_db(app)

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

# Import models to register them with SQLAlchemy
import models

# Import routes after app initialization to avoid circular imports
print("[DEBUG] Importing routes")
import routes

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Page not found: {error}')
    return {'status': 'error', 'message': 'Resource not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server error: {error}')
    db.session.rollback()
    return {'status': 'error', 'message': 'Internal server error'}, 500

if __name__ == '__main__':
    port = int(os.getenv('SERVER_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Use gevent WSGI server
    from gevent.pywsgi import WSGIServer
    http_server = WSGIServer(('0.0.0.0', port), app)
    http_server.serve_forever()
