from flask import Flask, render_template
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

import routes

def create_app():
    app = Flask(__name__)
    
    app.config.from_object('config.Config')
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    app.config['ENV'] = 'production'

    # Initialize extensions
    from models import db
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth_bp.login'
    CORS(app)

    # Initialize routes
    routes.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('error.html', error=error), 500

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
