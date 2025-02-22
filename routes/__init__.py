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
from .pages import pages_bp

# Define which blueprints are exposed
__all__ = [
    'auth_bp',
    'announcements_bp',
    'main',
    'pages_bp'
]

# Register child blueprints
def init_app(app):
    """Initialize application with all blueprints"""
    # Register pages blueprint for main routes
    app.register_blueprint(pages_bp)
    
    # Register other blueprints with their prefixes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(announcements_bp, url_prefix='/announcements')
    app.register_blueprint(main, url_prefix='/main')
