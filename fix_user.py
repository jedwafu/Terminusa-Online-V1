from flask import Flask
from database import db
from models.user import User
from sqlalchemy.orm import relationship, backref

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///test.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
db.init_app(app)

with app.app_context():
    # Add the relationship to the User model
    User.announcements = relationship('Announcement', 
                                     foreign_keys='Announcement.author_id',
                                     backref=backref('author', lazy='joined'),
                                     lazy='dynamic')
    
    print("Successfully modified User model")
