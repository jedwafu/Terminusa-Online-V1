from flask import Flask
from database import db
from models import User, Announcement

app = Flask(__name__)
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///test.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
db.init_app(app)

with app.app_context():
    db.create_all()
    print("Successfully created database tables")
