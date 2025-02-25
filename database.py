from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize the database"""
    db.init_app(app)
    with app.app_context():
        # Create tables in dependency order
        db.metadata.create_all(bind=db.engine, tables=[
            db.metadata.tables['users'],
            db.metadata.tables['player_characters'],
            db.metadata.tables['wallets'],
            db.metadata.tables['announcements']
        ])
