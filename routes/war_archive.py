from flask import Blueprint, jsonify, request, send_file, current_app
from flask_login import login_required, current_user
from datetime import datetime
import os

from models import db, Guild, GuildWar
from game_systems.war_archive import WarArchive

war_archive_bp = Blueprint('war_archive', __name__)
war_archive = None

@war_archive_bp.record
def record_war_archive(state):
    """Initialize war archive with app context"""
    global war_archive
    war_archive = WarArchive(state.app.websocket)

# Archive Access Routes
@war_archive_bp.route('/api/war/archive/<int:war_id>')
@login_required
def get_archived_war(war_id):
    """Get archived war data"""
    try:
        archive_data = war_archive.get_archived_war(war_id)
        if not archive_data:
            return jsonify({
                "success": False,
                "message": "Archive not found"
            }), 404

        # Check if user has access to this war archive
        guild_id = current_user.guild_id
        if guild_id not in [
            archive_data['metadata']['challenger_id'],
            archive_data['metadata']['target_id']
        ]:
            return jsonify({
                "success": False,
                "message": "Access denied"
            }), 403

        return jsonify({
            "success": True,
            "archive": archive_data
        })

    except Exception as e:
        current_app.logger.error(f"Archive retrieval error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to retrieve archive"
        }), 500

@war_archive_bp.route('/api/guild/<int:guild_id>/war-history')
@login_required
def get_guild_war_history(guild_id):
    """Get guild's war history"""
    try:
        # Check if user has access to guild history
        if guild_id != current_user.guild_id and not current_user.is_admin:
            return jsonify({
                "success": False,
                "message": "Access denied"
            }), 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        result = war_archive.get_guild_war_history(
            guild_id=guild_id,
            page=page,
            per_page=per_page
        )

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"War history error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to retrieve war history"
        }), 500

@war_archive_bp.route('/api/war/archive/<int:war_id>/download')
@login_required
def download_archive(war_id):
    """Download war archive file"""
    try:
        archive_data = war_archive.get_archived_war(war_id)
        if not archive_data:
            return jsonify({
                "success": False,
                "message": "Archive not found"
            }), 404

        # Check access permissions
        guild_id = current_user.guild_id
        if guild_id not in [
            archive_data['metadata']['challenger_id'],
            archive_data['metadata']['target_id']
        ] and not current_user.is_admin:
            return jsonify({
                "success": False,
                "message": "Access denied"
            }), 403

        # Get archive file path
        archive_path = war_archive._find_archive(war_id)
        if not archive_path:
            return jsonify({
                "success": False,
                "message": "Archive file not found"
            }), 404

        # Send file
        return send_file(
            archive_path,
            as_attachment=True,
            download_name=f"war_{war_id}_archive.json"
        )

    except Exception as e:
        current_app.logger.error(f"Archive download error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to download archive"
        }), 500

# Archive Management Routes
@war_archive_bp.route('/api/war/<int:war_id>/archive', methods=['POST'])
@login_required
def archive_war(war_id):
    """Archive a completed war"""
    try:
        # Check admin permissions
        if not current_user.is_admin:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403

        war = GuildWar.query.get(war_id)
        if not war:
            return jsonify({
                "success": False,
                "message": "War not found"
            }), 404

        result = war_archive.archive_war(war)
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"War archival error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to archive war"
        }), 500

@war_archive_bp.route('/api/war/archive/cleanup', methods=['POST'])
@login_required
def cleanup_archives():
    """Clean up old archives"""
    try:
        # Check admin permissions
        if not current_user.is_admin:
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403

        result = war_archive.cleanup_old_archives()
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Archive cleanup error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to clean up archives"
        }), 500

# Archive Statistics Routes
@war_archive_bp.route('/api/war/archive/stats')
@login_required
def get_archive_stats():
    """Get archive statistics"""
    try:
        stats = {
            'total_archives': 0,
            'total_size': 0,
            'oldest_archive': None,
            'newest_archive': None,
            'storage_usage': 0
        }

        # Count archives and calculate stats
        archive_dir = war_archive.archive_dir
        if archive_dir.exists():
            archives = list(archive_dir.glob('*.json*'))
            stats['total_archives'] = len(archives)
            
            if archives:
                # Calculate total size
                stats['total_size'] = sum(f.stat().st_size for f in archives)
                
                # Find oldest and newest archives
                archive_dates = [
                    datetime.fromtimestamp(f.stat().st_mtime)
                    for f in archives
                ]
                stats['oldest_archive'] = min(archive_dates).isoformat()
                stats['newest_archive'] = max(archive_dates).isoformat()
                
                # Calculate storage usage
                total_space = os.statvfs(archive_dir).f_blocks * os.statvfs(archive_dir).f_frsize
                used_space = stats['total_size']
                stats['storage_usage'] = (used_space / total_space) * 100

        return jsonify({
            "success": True,
            "stats": stats
        })

    except Exception as e:
        current_app.logger.error(f"Archive stats error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Failed to get archive statistics"
        }), 500

# Error Handlers
@war_archive_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': str(error)
    }), 400

@war_archive_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'message': 'Access denied'
    }), 403

@war_archive_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404

@war_archive_bp.errorhandler(500)
def server_error(error):
    current_app.logger.error(f'Server Error: {error}')
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500
