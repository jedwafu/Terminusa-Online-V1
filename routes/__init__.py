"""
Routes package initialization.
Exposes all route blueprints through a clean interface.
"""

from flask import Blueprint, render_template, current_app
from flask_login import current_user

# Import all blueprints
from .auth_routes import auth
from .announcements import announcements
from .main import main

# Define which blueprints are exposed
__all__ = [
    'auth',
    'announcements',
    'main'
]

# Register child blueprints
def init_app(app):
    """Initialize application with all blueprints"""
    # Register main blueprint
    app.register_blueprint(main, url_prefix='/')
    
    # Register auth blueprint
    app.register_blueprint(auth, url_prefix='/auth')
    
    # Register announcements blueprint
    app.register_blueprint(announcements, url_prefix='/announcements')
