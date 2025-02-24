from flask_restful import Api

from resources.routers import *
from .auth import *


def register_actions(app):
    api = Api(app)
    # для сайта
    api.add_resource(SignUp, '/api/auth/signup', strict_slashes=False)  #
    api.add_resource(AuthLogin, '/api/auth/login', strict_slashes=False)  #
    # api.add_resource(GameNew, '/api/game', strict_slashes=False)  #
    api.add_resource(GameWork, '/api/game/<id>', strict_slashes=False)  #
    api.add_resource(BetRouter, '/api/bet/<id>', strict_slashes=False)  #
    api.add_resource(HistoryBets, '/api/historybet', strict_slashes=False)  #
    api.add_resource(HistoryGames, '/api/games', strict_slashes=False)  #
    api.add_resource(UserInfo, '/api/user', strict_slashes=False)  #

    #
    # api.add_resource(GameOver, '/api/gameover/<id>', strict_slashes=False)  #
    api.add_resource(DepositRouter, '/api/deposit', '/api/deposit/<id>', strict_slashes=False)  #
    api.add_resource(PayoutRouter, '/api/payout', strict_slashes=False)
    api.add_resource(ActivatePromocodeRouter, '/api/activate_promocode', strict_slashes=False)  #
    api.add_resource(Payment, '/api/payment', strict_slashes=False)  #
    api.add_resource(MyBets, '/api/mybets', strict_slashes=False)  #
    api.add_resource(AllUsers, '/api/allusers', strict_slashes=False)  #
    api.add_resource(AdminPanel, '/api/adminpanel', strict_slashes=False)
    api.add_resource(TopBets, '/api/topbets', strict_slashes=False)

    # для бота
    api.add_resource(AdminRouter, '/api/bot/admin/<id>', strict_slashes=False)  # admin_id  #
    api.add_resource(BotUserWork, '/api/bot/user/<id>', strict_slashes=False)  # admin id   #
    api.add_resource(BalanceRouter, '/api/bot/balance/<id>', strict_slashes=False)  # user id   #
    api.add_resource(SignalRouter, '/api/bot/signal/<id>', strict_slashes=False)  #
    api.add_resource(PromocodeRouter, '/api/bot/promocode/<id>', strict_slashes=False)  # admin_id
    api.add_resource(BotUserInfo, '/api/bot/userinfo/<id>', strict_slashes=False)
    api.add_resource(ChangeUser, '/api/bot/changeuser/<id>', strict_slashes=False)  # user_Id
    api.add_resource(FakeRequisiteRouter, '/api/bot/fakerequisite/<id>', strict_slashes=False)  # admin_id
    api.add_resource(SettingAppRouter, '/api/bot/settingapp/<id>', strict_slashes=False)
    api.add_resource(BotMirror, '/api/bot/mirror/<id>', strict_slashes=False)  # admin_id
    api.add_resource(BotSettingRouter, '/api/bot/settingbot/<id>', strict_slashes=False)  # admin_id
