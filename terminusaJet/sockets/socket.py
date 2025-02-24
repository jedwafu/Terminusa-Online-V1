import time
from flask_socketio import SocketIO, emit
from database.models import GameModel
from schemas.sheme import GameSchema
from utils.crash import *


def sockets_add(app):
    socketio = SocketIO(app, cors_allowed_origins="*")

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('message', {'data': 'Connected'})

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('state')
    def handle_state():
        game = GameModel.query.order_by(GameModel._id.desc()).first()
        emit('state', GameSchema().dump(game))

    return socketio


def emit_game_updates(socketio, app):
    while True:
        with app.app_context():
            multiplier = AlgorithmCrash().get_result()
            game = GameModel(multiplier)
            game.save()
            flight_time = calculate_flight_time(game.multiplier) + 1
            socketio.emit('state', GameSchema().dump(game), namespace='/')
            socketio.sleep(14.5)
            game.state = 2
            game.save()
            socketio.emit('state', GameSchema().dump(game), namespace='/')
            time.sleep(flight_time)
            socketio.emit('gameFinished', GameSchema().dump(game), namespace='/')
            game.state = 3
            game.save()
            time.sleep(1)
