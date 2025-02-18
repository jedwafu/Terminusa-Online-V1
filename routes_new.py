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
            latest_announcements = Announcement.query.order_by(
                Announcement.created_at.desc()
            ).limit(3).all()

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
            
            announcements = Announcement.query.order_by(
                Announcement.created_at.desc()
            ).all()

            # Get current user if authenticated
            current_user = None
            if get_jwt_identity():
                current_user = User.query.filter_by(username=get_jwt_identity()).first()

            return render_template('announcements_updated.html',
                                title='Announcements',
                                announcements=announcements,
                                is_authenticated=get_jwt_identity() is not None,
                                current_user=current_user)
        except Exception as e:
            logger.error(f"Error rendering announcements page: {str(e)}")
            return render_template('error.html',
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
