"""Main routes blueprint"""
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from models import User, Announcement
from database import db

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
def index():
    """Main landing page"""
    try:
        # Check JWT but don't require it
        verify_jwt_in_request(optional=True)
        
        # Get latest announcements for the news section
        latest_announcements = []
        try:
            latest_announcements = Announcement.query.order_by(
                Announcement.created_at.desc()
            ).limit(3).all()
        except Exception as e:
            current_app.logger.warning(f"Failed to fetch announcements: {str(e)}")
            # Create the table if it doesn't exist
            if "relation \"announcements\" does not exist" in str(e):
                try:
                    db.create_all()
                    db.session.commit()
                    current_app.logger.info("Created announcements table")
                except Exception as create_error:
                    current_app.logger.error(f"Failed to create announcements table: {str(create_error)}")

        # Get current user if authenticated
        current_user = None
        if get_jwt_identity():
            current_user = User.query.filter_by(username=get_jwt_identity()).first()

        return render_template('index.html', 
                            title='Home',
                            latest_announcements=latest_announcements,
                            is_authenticated=get_jwt_identity() is not None,
                            current_user=current_user)
    except Exception as e:
        current_app.logger.error(f"Error rendering index page: {str(e)}")
        current_app.logger.exception(e)  # Log full traceback
        return render_template('error.html',
                            error_message='Failed to load page. Please try again later.',
                            title='Error',
                            is_authenticated=False), 500

@main.route('/play')
@jwt_required()
def play():
    """Game client page"""
    try:
        return redirect('https://play.terminusa.online', code=301)
    except Exception as e:
        current_app.logger.error(f"Error redirecting to game client: {str(e)}")
        return render_template('error.html',
                            error_message='Failed to load game client. Please try again later.',
                            title='Error'), 500

@main.route('/marketplace')
@jwt_required()
def marketplace():
    """Marketplace page"""
    try:
        return render_template('marketplace.html', title='Marketplace')
    except Exception as e:
        current_app.logger.error(f"Error rendering marketplace page: {str(e)}")
        return render_template('error.html',
                            error_message='Failed to load marketplace. Please try again later.',
                            title='Error'), 500

@main.route('/gates')
@jwt_required()
def gates():
    """Gates page"""
    try:
        return render_template('gates.html', title='Gates')
    except Exception as e:
        current_app.logger.error(f"Error rendering gates page: {str(e)}")
        return render_template('error.html',
                            error_message='Failed to load gates. Please try again later.',
                            title='Error'), 500

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
