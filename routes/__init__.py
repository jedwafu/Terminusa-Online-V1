"""
Routes package initialization.
Exposes all route blueprints through a clean interface.
"""

from flask import Blueprint, render_template, current_app
from flask_login import current_user

# Import all blueprints
from .auth_routes import auth

# Define which blueprints are exposed
__all__ = [
    'auth'
]

# Create a main blueprint for the application
main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Main index route"""
    return render_template('index.html')

# Error handlers
@main.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    current_app.logger.error(f'Page not found: {error}')
    return render_template('error.html',
                         error_code=404,
                         title='Page Not Found',
                         error_message='The page you are looking for could not be found.'), 404

@main.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    current_app.logger.error(f'Server error: {error}')
    return render_template('error.html',
                         error_code=500,
                         title='Server Error',
                         error_message='An unexpected error has occurred. Please try again later.'), 500

# Register child blueprints
def init_app(app):
    """Initialize application with all blueprints"""
    # Register main blueprint
    app.register_blueprint(main)
    
    # Register auth blueprint
    app.register_blueprint(auth, url_prefix='/auth')
