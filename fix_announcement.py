from flask import Flask
from database import db
from models.announcement import Announcement
from sqlalchemy.orm import relationship, backref

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///test.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
db.init_app(app)

with app.app_context():
    # Modify the Announcement model's author relationship
    Announcement.author = relationship('User', foreign_keys=[Announcement.author_id], backref=backref('authored_announcements', lazy='dynamic'))
    
    print("Successfully modified Announcement model")
