from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Create the SQLAlchemy instance
db = SQLAlchemy()
migrate = None

def init_db(app):
    """Initialize the database with the Flask app"""
    global migrate
    db.init_app(app)
    migrate = Migrate(app, db)
    
    with app.app_context():
        db.create_all()
