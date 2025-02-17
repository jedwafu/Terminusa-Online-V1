from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from database import db, init_db
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure app
app.config.update(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY'),
    JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY'),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# Initialize database
init_db(app)

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Registration page"""
    return render_template('register.html')

@app.route('/play')
def play_page():
    """Game page"""
    return render_template('play.html')

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
    port = int(os.getenv('WEBAPP_PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
