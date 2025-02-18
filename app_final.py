from gevent import monkey
monkey.patch_all()

import os
from flask import Flask, render_template, send_from_directory, make_response, current_app
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from database import db, init_db
import mimetypes

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
    STATIC_FOLDER=os.path.abspath('static')  # Use absolute path
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

# Static file serving
def send_static_file(filename, directory=''):
    """Helper function to send static files with proper MIME types and headers."""
    try:
        path = os.path.join(current_app.config['STATIC_FOLDER'], directory, filename)
        if not os.path.isfile(path):
            current_app.logger.error(f'Static file not found: {path}')
            return '', 404

        mime_type = None
        if filename.endswith('.css'):
            mime_type = 'text/css'
        elif filename.endswith('.js'):
            mime_type = 'application/javascript'
        else:
            mime_type = mimetypes.guess_type(filename)[0]

        response = make_response(send_from_directory(
            os.path.join(current_app.config['STATIC_FOLDER'], directory),
            filename,
            conditional=True
        ))

        if mime_type:
            response.headers['Content-Type'] = f'{mime_type}; charset=utf-8'
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        current_app.logger.info(f'Serving static file: {filename} ({mime_type})')
        return response
    except Exception as e:
        current_app.logger.error(f'Error serving static file {filename}: {str(e)}')
        return '', 404

@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_static_file(filename, 'css')

@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_static_file(filename, 'js')

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    return send_static_file(filename, 'images')

@app.route('/static/<path:filename>')
def serve_static_root(filename):
    return send_static_file(filename)

# Import models and routes
import models
from routes_final import init_routes

# Initialize routes
init_routes(app)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Page not found: {error}')
    return render_template('error_single.html',
                         error_message='The page you are looking for could not be found.',
                         title='404 Not Found',
                         is_authenticated=False,
                         extra_css='error_single.css'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server error: {error}')
    db.session.rollback()
    return render_template('error_single.html',
                         error_message='An internal server error occurred. Please try again later.',
                         title='500 Server Error',
                         is_authenticated=False,
                         extra_css='error_single.css'), 500

if __name__ == '__main__':
    port = int(os.getenv('SERVER_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Use gevent WSGI server
    from gevent.pywsgi import WSGIServer
    http_server = WSGIServer(('0.0.0.0', port), app)
    http_server.serve_forever()
