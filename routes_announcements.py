from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Announcement, User
from datetime import datetime
from functools import wraps

announcements = Blueprint('announcements', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Public routes
@announcements.route('/announcements')
def announcements_page():
    """Display all active announcements to users"""
    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.priority.desc(), Announcement.created_at.desc())\
        .all()
    return render_template('announcements.html', announcements=announcements)

# Admin routes
@announcements.route('/admin/announcements')
@login_required
@admin_required
def admin_announcements():
    """Admin interface for managing announcements"""
    announcements = Announcement.query.order_by(
        Announcement.priority.desc(),
        Announcement.created_at.desc()
    ).all()
    return render_template('admin/announcements.html', announcements=announcements)

@announcements.route('/admin/announcements/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_announcement():
    """Create a new announcement"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        priority = request.form.get('priority', 0, type=int)
        
        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('announcements.create_announcement'))
        
        announcement = Announcement(
            title=title,
            content=content,
            priority=priority,
            author_id=current_user.id
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('announcements.admin_announcements'))
    
    return render_template('admin/create_announcement.html')

@announcements.route('/admin/announcements/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_announcement(id):
    """Edit an existing announcement"""
    announcement = Announcement.query.get_or_404(id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        priority = request.form.get('priority', 0, type=int)
        is_active = request.form.get('is_active') == 'true'
        
        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('announcements.edit_announcement', id=id))
        
        announcement.title = title
        announcement.content = content
        announcement.priority = priority
        announcement.is_active = is_active
        announcement.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Announcement updated successfully!', 'success')
        return redirect(url_for('announcements.admin_announcements'))
    
    return render_template('admin/edit_announcement.html', announcement=announcement)

@announcements.route('/admin/announcements/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_announcement(id):
    """Delete an announcement"""
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    
    flash('Announcement deleted successfully!', 'success')
    return redirect(url_for('announcements.admin_announcements'))

@announcements.route('/admin/announcements/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_announcement(id):
    """Toggle announcement active status"""
    announcement = Announcement.query.get_or_404(id)
    announcement.is_active = not announcement.is_active
    db.session.commit()
    
    status = 'activated' if announcement.is_active else 'deactivated'
    flash(f'Announcement {status} successfully!', 'success')
    return redirect(url_for('announcements.admin_announcements'))

# API routes for AJAX operations
@announcements.route('/api/announcements/<int:id>', methods=['GET'])
def get_announcement(id):
    """Get announcement details"""
    announcement = Announcement.query.get_or_404(id)
    return jsonify({
        'id': announcement.id,
        'title': announcement.title,
        'content': announcement.content,
        'priority': announcement.priority,
        'is_active': announcement.is_active,
        'created_at': announcement.created_at.isoformat(),
        'updated_at': announcement.updated_at.isoformat() if announcement.updated_at else None,
        'author': announcement.author.username
    })

@announcements.route('/api/announcements/latest', methods=['GET'])
def get_latest_announcements():
    """Get latest active announcements"""
    limit = request.args.get('limit', 5, type=int)
    announcements = Announcement.query.filter_by(is_active=True)\
        .order_by(Announcement.priority.desc(), Announcement.created_at.desc())\
        .limit(limit)\
        .all()
    
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'content': a.content,
        'created_at': a.created_at.isoformat(),
        'author': a.author.username
    } for a in announcements])
