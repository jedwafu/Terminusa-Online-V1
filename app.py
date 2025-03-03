"""
Main Application for Terminusa Online
"""
import os
from datetime import datetime
import logging
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from models import db, User
from game_manager import GameManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object('config.Config')

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# Initialize game manager
game_manager = GameManager()

@app.before_request
def before_request():
    """Set up request context"""
    g.start_time = datetime.utcnow()

@app.after_request
def after_request(response):
    """Log request details"""
    if hasattr(g, 'start_time'):
        duration = datetime.utcnow() - g.start_time
        logger.info(
            f"{request.method} {request.path} - {response.status_code} "
            f"- Duration: {duration.total_seconds():.3f}s"
        )
    return response

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    logger.error(f"Unhandled error: {str(error)}", exc_info=True)
    return jsonify({
        "success": False,
        "message": "An unexpected error occurred"
    }), 500

# Game action endpoint
@app.route('/api/game/action', methods=['POST'])
@jwt_required()
def game_action():
    """Handle game actions"""
    try:
        # Get user from JWT
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        # Get action details
        data = request.get_json()
        action = data.get('action')
        params = data.get('params', {})

        if not action:
            return jsonify({
                "success": False,
                "message": "No action specified"
            }), 400

        # Process action through game manager
        result = game_manager.process_user_action(user, action, params)
        
        # Include updated user state in response
        if result["success"]:
            result["state"] = game_manager.get_user_state(user)["state"]

        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to process game action: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "Failed to process game action"
        }), 500

# Get user state endpoint
@app.route('/api/game/state', methods=['GET'])
@jwt_required()
def get_state():
    """Get user's game state"""
    try:
        # Get user from JWT
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        # Get state through game manager
        result = game_manager.get_user_state(user)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to get game state: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "message": "Failed to get game state"
        }), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Initialize database tables
def init_db():
    """Initialize database tables"""
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Initialize database
    init_db()
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )
