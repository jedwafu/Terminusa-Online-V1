from flask import render_template, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from models import User, Announcement
from database import db
import logging

logger = logging.getLogger(__name__)

def init_routes(app):
    @app.route('/')
    @app.route('/index')
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
                logger.warning(f"Failed to fetch announcements: {str(e)}")
                # Create the table if it doesn't exist
                if "relation \"announcements\" does not exist" in str(e):
                    try:
                        db.create_all()
                        db.session.commit()
                        logger.info("Created announcements table")
                    except Exception as create_error:
                        logger.error(f"Failed to create announcements table: {str(create_error)}")

            # Get current user if authenticated
            current_user = None
            if get_jwt_identity():
                current_user = User.query.filter_by(username=get_jwt_identity()).first()

            return render_template('index_new.html', 
                                title='Home',
                                latest_announcements=latest_announcements,
                                is_authenticated=get_jwt_identity() is not None,
                                current_user=current_user)
        except Exception as e:
            logger.error(f"Error rendering index page: {str(e)}")
            logger.exception(e)  # Log full traceback
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/announcements')
    def announcements_page():
        """Render announcements page"""
        try:
            # Check JWT but don't require it
            verify_jwt_in_request(optional=True)
            
            announcements = []
            try:
                announcements = Announcement.query.order_by(
                    Announcement.created_at.desc()
                ).all()
            except Exception as e:
                logger.warning(f"Failed to fetch announcements: {str(e)}")
                # Create the table if it doesn't exist
                if "relation \"announcements\" does not exist" in str(e):
                    try:
                        db.create_all()
                        db.session.commit()
                        logger.info("Created announcements table")
                    except Exception as create_error:
                        logger.error(f"Failed to create announcements table: {str(create_error)}")

            # Get current user if authenticated
            current_user = None
            if get_jwt_identity():
                current_user = User.query.filter_by(username=get_jwt_identity()).first()

            return render_template('announcements_merged.html',
                                title='Announcements',
                                announcements=announcements,
                                is_authenticated=get_jwt_identity() is not None,
                                current_user=current_user)
        except Exception as e:
            logger.error(f"Error rendering announcements page: {str(e)}")
            return render_template('error_new.html',
                                error_message='Failed to load announcements. Please try again later.'), 500

    @app.route('/announcements', methods=['POST'])
    @jwt_required()
    def create_announcement():
        """Create a new announcement - requires admin access"""
        try:
            # Get current user
            current_user = User.query.filter_by(username=get_jwt_identity()).first()
            if not current_user or current_user.role != 'admin':
                return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

            data = request.get_json()
            if not data or 'title' not in data or 'content' not in data:
                return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

            new_announcement = Announcement(
                title=data['title'],
                content=data['content'],
                created_at=datetime.utcnow()
            )
            db.session.add(new_announcement)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Announcement created successfully',
                'announcement': {
                    'id': new_announcement.id,
                    'title': new_announcement.title,
                    'content': new_announcement.content,
                    'created_at': new_announcement.created_at.isoformat()
                }
            }), 201
        except Exception as e:
            logger.error(f"Error creating announcement: {str(e)}")
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'Failed to create announcement'}), 500

    @app.route('/announcements/<int:id>', methods=['PUT'])
    @jwt_required()
    def update_announcement(id):
        """Update an existing announcement - requires admin access"""
        try:
            # Get current user
            current_user = User.query.filter_by(username=get_jwt_identity()).first()
            if not current_user or current_user.role != 'admin':
                return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

            announcement = Announcement.query.get(id)
            if not announcement:
                return jsonify({'status': 'error', 'message': 'Announcement not found'}), 404

            data = request.get_json()
            if not data or 'title' not in data or 'content' not in data:
                return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

            announcement.title = data['title']
            announcement.content = data['content']
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Announcement updated successfully',
                'announcement': {
                    'id': announcement.id,
                    'title': announcement.title,
                    'content': announcement.content,
                    'created_at': announcement.created_at.isoformat()
                }
            }), 200
        except Exception as e:
            logger.error(f"Error updating announcement: {str(e)}")
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'Failed to update announcement'}), 500

    @app.route('/announcements/<int:id>', methods=['DELETE'])
    @jwt_required()
    def delete_announcement(id):
        """Delete an announcement - requires admin access"""
        try:
            # Get current user
            current_user = User.query.filter_by(username=get_jwt_identity()).first()
            if not current_user or current_user.role != 'admin':
                return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

            announcement = Announcement.query.get(id)
            if not announcement:
                return jsonify({'status': 'error', 'message': 'Announcement not found'}), 404

            db.session.delete(announcement)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Announcement deleted successfully'
            }), 200
        except Exception as e:
            logger.error(f"Error deleting announcement: {str(e)}")
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'Failed to delete announcement'}), 500
<environment_details>
# VSCode Visible Files
routes_merged.py

# VSCode Open Tabs
run_server.py
email_service.py
setup_smtp.sh
start_server.bat
client/client.py
client/requirements.txt
client/setup.sh
client/setup.bat
client/README.md
migrations/versions/002_update_gate_model.py
alembic.ini
migrations/env.py
static/js/marketplace_new.js
templates/base_updated.html
.env.example
.env
create_initial_announcement.py
app.py
static/css/login_new.css
templates/login_updated.html
templates/error_new.html
setup_db_user.sh
main.py
static/css/main.css
templates/base.html
static/css/base_new.css
templates/announcements_updated.html
static/css/announcements_updated.css
templates/index_new.html
templates/register_new.html
templates/marketplace_new.html
templates/leaderboard_new.html
migrations/versions/005_create_announcements.py
migrations/versions/006_add_announcements_only.py
create_sample_announcement.py
database.py
migrations/versions/004_add_missing_tables.py
requirements-updated.txt
static/css/base.css
templates/index.html
static/css/marketplace.css
plan.md
web_app_updated.py
migrations/versions/003_add_user_model.py
create_admin_user.py
README_update.md
announcements.patch
routes_announcements.py
routes_minimal.py
static/css/announcements.css
templates/announcements_new.html
models.py
start_server.sh
nginx/terminusa.conf
deploy_new.sh
templates/base_new.html
static/css/base_merged.css
templates/base_merged.html
app_new.py
templates/announcements_merged.html
routes_merged.py
models_with_announcements.py
templates/index_updated.html
templates/base_fixed.html
templates/index_fixed.html
templates/message_fixed.html
templates/marketplace_fixed.html
templates/login_fixed.html
templates/leaderboard_fixed.html
templates/register.html
templates/play_fixed.html
create_admin.py
static/js/main.js
init_db.py
templates/leaderboard.html
static/js/marketplace.js
static/js/leaderboard.js
templates/play.html
server_manager.py
client.py
</environment_details>
