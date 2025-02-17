from flask import Flask, request, jsonify, render_template
from models import Announcement
from database import db

app = Flask(__name__)

@app.route('/announcements', methods=['GET'])
def get_announcements():
    announcements = Announcement.query.all()
    return render_template('announcements.html', announcements=announcements)

@app.route('/announcements', methods=['POST'])
def create_announcement():
    # Check if the user is an admin
    if not request.user.is_admin:
        return jsonify({'message': 'Unauthorized access!'}), 403
    data = request.get_json()
    new_announcement = Announcement(title=data['title'], content=data['content'])
    db.session.add(new_announcement)
    db.session.commit()
    return jsonify({'message': 'Announcement created!'}), 201

@app.route('/announcements/<int:id>', methods=['PUT'])
def update_announcement(id):
    data = request.get_json()
    announcement = Announcement.query.get(id)
    if announcement:
        announcement.title = data['title']
        announcement.content = data['content']
        db.session.commit()
        return jsonify({'message': 'Announcement updated!'}), 200
    return jsonify({'message': 'Announcement not found!'}), 404

@app.route('/announcements/<int:id>', methods=['DELETE'])
def delete_announcement(id):
    announcement = Announcement.query.get(id)
    if announcement:
        db.session.delete(announcement)
        db.session.commit()
        return jsonify({'message': 'Announcement deleted!'}), 200
    return jsonify({'message': 'Announcement not found!'}), 404

if __name__ == '__main__':
    app.run(debug=True)
