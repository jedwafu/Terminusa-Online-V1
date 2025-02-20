"""
Routes package initialization.
Exposes all route blueprints through a clean interface.
"""

from flask import Blueprint

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
    return 'Welcome to Terminusa Online'

# Register child blueprints
def init_app(app):
    """Initialize application with all blueprints"""
    # Register main blueprint
    app.register_blueprint(main)
    
    # Register auth blueprint
    app.register_blueprint(auth, url_prefix='/auth')
