"""
Routes package initialization.
Exposes all route blueprints through a clean interface.
"""

from flask import Blueprint, render_template, current_app
from flask_login import current_user

# Import all blueprints
from .auth_routes import auth_bp
from .announcements import announcements_bp
from .main import main

# Define which blueprints are exposed
__all__ = [
    'auth_bp',
    'announcements_bp',
    'main'
]

# Register child blueprints
def init_app(app):
    """Initialize application with all blueprints"""
    # Register main blueprint
    app.register_blueprint(main)  # No url_prefix for main routes
    
    # Register auth blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Register announcements blueprint
    app.register_blueprint(announcements_bp, url_prefix='/announcements')
