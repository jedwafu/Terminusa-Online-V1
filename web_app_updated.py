from flask import Flask, request, jsonify, render_template, session
from models import Announcement, User
from database import db
from functools import wraps

app = Flask(__name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'message': 'Authentication required!'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'message': 'Admin privileges required!'}), 403
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/announcements', methods=['GET'])
def get_announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    user = None
    if session.get('user_id'):
        user = User.query.get(session['user_id'])
    return render_template('announcements.html', 
                         announcements=announcements,
                         is_admin=user.is_admin if user else False)

@app.route('/announcements', methods=['POST'])
@admin_required
def create_announcement():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'message': 'Missing required fields!'}), 400
        
    new_announcement = Announcement(
        title=data['title'],
        content=data['content']
    )
    db.session.add(new_announcement)
    db.session.commit()
    return jsonify({'message': 'Announcement created successfully!'}), 201

@app.route('/announcements/<int:id>', methods=['PUT'])
@admin_required
def update_announcement(id):
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'message': 'Missing required fields!'}), 400
        
    announcement = Announcement.query.get(id)
    if not announcement:
        return jsonify({'message': 'Announcement not found!'}), 404
        
    announcement.title = data['title']
    announcement.content = data['content']
    db.session.commit()
    return jsonify({'message': 'Announcement updated successfully!'}), 200

@app.route('/announcements/<int:id>', methods=['DELETE'])
@admin_required
def delete_announcement(id):
    announcement = Announcement.query.get(id)
    if not announcement:
        return jsonify({'message': 'Announcement not found!'}), 404
        
    db.session.delete(announcement)
    db.session.commit()
    return jsonify({'message': 'Announcement deleted successfully!'}), 200

if __name__ == '__main__':
    app.run(debug=True)
