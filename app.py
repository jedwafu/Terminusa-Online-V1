from flask import Flask, render_template
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import emit

import routes
from websocket_manager import WebSocketManager

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize extensions
    from models import db
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth_bp.login'
    CORS(app)
    
    # Initialize WebSocket manager
    websocket = WebSocketManager(app)
    app.websocket = websocket

    # Initialize routes
    routes.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # WebSocket event handlers
    @websocket.socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            app.logger.info(f'User {current_user.id} connected')
            emit('connection_success', {'message': 'Connected successfully'})
        else:
            return False

    @websocket.socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            app.logger.info(f'User {current_user.id} disconnected')

    @websocket.socketio.on_error_default
    def default_error_handler(e):
        app.logger.error(f'WebSocket error: {str(e)}')

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html', error=error), 500

    # Context processors
    @app.context_processor
    def utility_processor():
        def format_currency(value):
            return "{:,.2f}".format(float(value))
            
        def format_timestamp(timestamp):
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
        return dict(
            format_currency=format_currency,
            format_timestamp=format_timestamp
        )

    # Before request handlers
    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            # Update last seen timestamp
            current_user.update_last_seen()
            db.session.commit()

    # After request handlers
    @app.after_request
    def after_request(response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response

    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        from models import (
            User, Mount, Pet, Item, Transaction,
            Gate, Guild, Quest, Achievement
        )
        return {
            'db': db,
            'User': User,
            'Mount': Mount,
            'Pet': Pet,
            'Item': Item,
            'Transaction': Transaction,
            'Gate': Gate,
            'Guild': Guild,
            'Quest': Quest,
            'Achievement': Achievement
        }

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.websocket.run(host='0.0.0.0', port=5000, debug=True)
