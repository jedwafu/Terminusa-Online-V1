from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager

from database.models import *
from resources.actions import register_actions
from resources.errors import Errors
from sockets.socket import *


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    Migrate(app, db)
    with app.app_context():
        # db.drop_all()
        db.create_all()
    JWTManager(app)
    CORS(app)
    Marshmallow(app)
    register_actions(app)
    Errors(app)
    socketio = sockets_add(app)
    # Запуск фоновой задачи после запуска сервера
    socketio.start_background_task(target=emit_game_updates, socketio=socketio, app=app)
    return app, socketio
