from flask import Flask, render_template, current_app
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import logging

import routes

def create_app():
    app = Flask(__name__, 
                template_folder='/var/www/terminusa/templates',
                static_folder='/var/www/terminusa/static')
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    # Configure app
    app.config.from_object('config.Config')
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    app.config['ENV'] = 'production'

    # Initialize extensions
    from models import db
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth_bp.login'
    CORS(app)

    # Initialize routes
    routes.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f'404 Error: {error}')
        return render_template('error.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'500 Error: {error}')
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
        app.logger.info('Processing request')
        if current_user.is_authenticated:
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
        
        app.logger.info(f'Request completed with status {response.status_code}')
        return response

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.logger.info('Starting application')
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
