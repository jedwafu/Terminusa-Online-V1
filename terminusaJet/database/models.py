import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime
from sqlalchemy import text, event
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.engine import Engine
from werkzeug.security import generate_password_hash
import uuid
import random

load_dotenv()
db = SQLAlchemy()


def execute_data(query: str):
    result = db.session.execute(text(query))
    return result.fetchall()


# @event.listens_for(Engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA foreign_keys=ON")
#     cursor.close()


class Base:
    def save(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete(self) -> None:
        db.session.delete(self)
        db.session.commit()


class PayoutModel(db.Model, Base):
    __tablename__ = "payout_methods"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(256), nullable=False, unique=True)
    description = db.Column(db.String(256), nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    block_payout = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, name, description, verified, block_payout):
        self.name = name
        self.description = description
        self.verified = verified
        self.block_payout = block_payout


class UsersModel(db.Model, Base):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0)
    admin = db.Column(db.Boolean, default=False)
    block_bet = db.Column(db.Boolean, nullable=False, default=False)
    block_payout = db.Column(db.Boolean, nullable=False, default=False)
    referal = db.Column(BIGINT, db.ForeignKey('admins.telegram_id',
                                              onupdate='CASCADE', ondelete='CASCADE'))
    verification = db.Column(db.Boolean, nullable=False, default=False)
    _id = db.Column(db.String(256), nullable=False, default=uuid.uuid4().hex)
    payout_method_id = db.Column(db.Integer, db.ForeignKey('payout_methods.id',
                                                           onupdate='CASCADE',
                                                           ondelete='CASCADE'),
                                 nullable=False, default=1)

    def __init__(self, login: str, email: str, password: str, referal: int = None) -> None:
        self.login = login
        self.email = email
        self.password = generate_password_hash(password)
        if referal is not None:
            self.referal = referal

    @classmethod
    def find_by_login(cls, login: str) -> 'UsersModel':
        return cls.query.filter_by(login=login).first()


class GameModel(db.Model, Base):
    __tablename__ = 'games'
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    multiplier = db.Column(db.Float, nullable=False, default=0.0)  # Изменено на nullable=True
    state = db.Column(db.Integer, nullable=False, default=1)
    id = db.Column(db.Integer, default=lambda: random.randint(1, 99999), nullable=False)

    def __init__(self, multiplier: int = None) -> None:
        self.multiplier = multiplier

    def __repr__(self):
        return f'{self._id}, {self.multiplier}, {self.state}, {self.id}'

class BetModel(db.Model, Base):
    __tablename__ = 'bets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE',
                                                  ondelete='CASCADE'), nullable=False)
    game_id = db.Column(db.Integer)
    amount = db.Column(db.Integer, nullable=False)
    multiplier = db.Column(db.Float, default=1)
    win = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, user_id: int, game_id: int, amount: int) -> None:
        self.user_id = user_id
        self.game_id = game_id
        self.amount = amount


# bot
class AdminModel(db.Model, Base):
    __tablename__ = 'admins'
    telegram_id = db.Column(BIGINT, primary_key=True)
    referal_url = db.Column(db.String(256), nullable=False)

    def __init__(self, telegram_id: int) -> None:
        self.telegram_id = telegram_id
        self.referal_url = f'https://t.me/{os.environ.get("BOT_USERNAME")}?start={telegram_id}'


class ReferalPromocodesModel(db.Model, Base):
    __tablename__ = 'referal_promocodes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    word = db.Column(db.String(256), nullable=False)
    bonus = db.Column(db.Integer, nullable=False, default=100)
    admin_id = db.Column(BIGINT, db.ForeignKey('admins.telegram_id'))

    def __init__(self, number: int):
        self.word = 'luckyjet' + str(number)
        self.admin_id = number

    @classmethod
    def find_admin_by_promocode(cls, promocode: str):
        return cls.query.filter_by(word=promocode).first()


class RequisiteModel(db.Model, Base):
    __tablename__ = 'requisites'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(256), nullable=False, unique=True)
    card = db.Column(db.String(256), nullable=False)

    def __init__(self, type: str, card: str) -> None:
        self.type = type
        self.card = card

    @classmethod
    def find_by_type(cls, type: str):
        return cls.query.filter_by(type=type).first()


class DepositModel(db.Model, Base):
    __tablename__ = 'deposits'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
                        nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    sum_payment = db.Column(db.Float, nullable=False)
    requisite_id = db.Column(db.Integer, db.ForeignKey('requisites.id', onupdate='CASCADE',
                                                       ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, user_id: int, amount: int, sum_payment: int, requisite_id: int) -> None:
        self.user_id = user_id
        self.amount = amount
        self.sum_payment = sum_payment
        self.requisite_id = requisite_id


class PromocodesModel(db.Model, Base):
    __tablename__ = "promocodes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    word = db.Column(db.String(256), nullable=False)
    admin_id = db.Column(BIGINT, db.ForeignKey('admins.telegram_id', onupdate='CASCADE', ondelete='CASCADE'),
                         nullable=False)
    type = db.Column(db.String(256), nullable=False)
    bonus = db.Column(db.Integer, nullable=False)
    count = db.Column(db.Integer, nullable=False)

    def __init__(self, word: str, admin_id: int, type: str, bonus: int, count: int) -> None:
        self.word = word
        self.admin_id = admin_id
        self.type = type
        self.bonus = bonus
        self.count = count

    @classmethod
    def find_by_word(cls, word: str):
        return cls.query.filter_by(word=word).first()


class ActivatedPromocodeModel(db.Model, Base):
    __tablename__ = "activated_promocodes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False)
    promocode_id = db.Column(db.Integer, db.ForeignKey('promocodes.id', onupdate='CASCADE', ondelete='CASCADE'),
                             nullable=False)
    status = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, user_id: int, promocode_id: int):
        self.user_id = user_id
        self.promocode_id = promocode_id

    def __repr__(self):
        return f'promocode_id:{self.user_id}, user_id:{self.user_id}, status:{self.status}'


class SettingAppModel(db.Model, Base):
    __tablename__ = 'settingsapp'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    min_deposit = db.Column(db.Integer, nullable=False, default=1000)
    min_output = db.Column(db.Integer, nullable=False, default=10000)
    stop_limit = db.Column(db.Integer, nullable=False, default=100000)
    notifications = db.Column(db.Boolean, nullable=False, default=True)
    notifications_bet = db.Column(db.Boolean, nullable=False, default=False)
    admin_id = db.Column(BIGINT, db.ForeignKey('admins.telegram_id', onupdate='CASCADE', ondelete='CASCADE'),
                         nullable=False)

    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    @classmethod
    def find_by_admin_id(cls, admin_id: int) -> "SettingAppModel":
        return cls.query.filter(cls.admin_id == admin_id).first()


class SettingBotModel(db.Model, Base):
    __tablename__ = 'settingsbot'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    count_signals = db.Column(db.Integer, nullable=False, default=5)
    support = db.Column(db.String(256))
    referal_system = db.Column(db.Boolean, nullable=False, default=True)
    admin_id = db.Column(BIGINT, db.ForeignKey('admins.telegram_id', onupdate='CASCADE', ondelete='CASCADE'),
                         nullable=False)

    def __init__(self, admin_id: int):
        self.admin_id = admin_id


class FakeRequisitesModel(db.Model, Base):
    __tablename__ = 'fake_requisites'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(256), nullable=False)
    card = db.Column(db.String(256), nullable=False)
    admin_id = db.Column(BIGINT, db.ForeignKey('admins.telegram_id', onupdate='CASCADE',
                                               ondelete='CASCADE'), nullable=False)

    def __init__(self, type: str, card: str, admin_id: int):
        self.type = type
        self.card = card
        self.admin_id = admin_id

    @classmethod
    def find_by_data(cls, type: str, admin_id):
        return cls.query.filter_by(type=type, admin_id=admin_id).first()

    @classmethod
    def find_by_card(cls, card: str, admin_id: int):
        return cls.query.filter_by(card=card, admin_id=admin_id).first()


class MirrorBotModel(db.Model, Base):
    __tablename__ = 'mirrors_bot'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(256), nullable=False)
    token = db.Column(db.String(256), nullable=False)
    admin_id = db.Column(BIGINT, db.ForeignKey('admins.telegram_id', onupdate='CASCADE',
                                               ondelete='CASCADE'), nullable=False)

    def __init__(self, token: str, username: str, admin_id: int) -> None:
        self.token = token
        self.url = f'@{username}'
        self.admin_id = admin_id

    @classmethod
    def find_by_data(cls, token: str, admin_id):
        return cls.query.filter_by(token=token, admin_id=admin_id).first()


class UsersSignalsModel(db.Model, Base):
    __tablename__ = 'users_signals'
    user_id = db.Column(BIGINT, primary_key=True)
    admin_id = db.Column(BIGINT, db.ForeignKey('admins.telegram_id', onupdate='CASCADE',
                                                   ondelete='CASCADE'))
    game_id = db.Column(db.Integer, default=0, nullable=False)
    count = db.Column(db.Integer, nullable=False, default=1)
    day = db.Column(db.Integer, nullable=False, default=datetime.now().day)

    def __init__(self, user_id: int, admin_id: int = None, game_id: int = None) -> None:
        self.user_id = user_id
        self.admin_id = admin_id
        if game_id is not None:
            self.game_id = game_id


class TopBetsModel(db.Model, Base):
    __tablename__ = 'top_bets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(256), nullable=False)
    bet = db.Column(db.Integer, nullable=False)
    multiplier = db.Column(db.Float, nullable=False)

    def __init__(self, username: str, bet: int, multiplier: float) -> None:
        self.username = username
        self.bet = bet
        self.multiplier = multiplier
