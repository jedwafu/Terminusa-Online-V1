from flask_restful import Resource
from flask import jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_socketio import emit

from faker import Faker
import random

from database.models import *
from schemas.sheme import *
from utils.crash import AlgorithmCrash
from utils.fake_requisite import *
from utils.send_message import *

import requests


# class GameNew(Resource):
#     def post(self):
#         try:
#             multiplier = AlgorithmCrash().get_result()
#             game = GameModel(multiplier=multiplier)
#             game.save()
#             emit('state', GameSchema().dump(game))
#         except Exception as e:
#             print(e)
#             return make_response(jsonify({'error': str(e)}), 500)
# class GameOver(Resource):
#     def post(self, id):  # game_id
#         try:
#             multiplier = request.json.get("multiplier")
#             bets = BetModel.query.filter_by(game_id=id).all()
#             if not bets:
#                 return make_response(jsonify({'message': 'Bets not found'}), 404)
#             game = GameModel(multiplier)
#             game.save()
#             for i in bets:
#                 if i.win is True:
#                     sum = round((i.amount * i.multiplier), 2)
#                     user = UsersModel.query.get(i.user_id)
#                     user.balance += sum
#                     user.save()
#             return make_response(jsonify({'message': 'success'}), 200)
#         except Exception as e:
#             return make_response(jsonify({'error': str(e)}))


# class GameNew(Resource):
#     def post(self):
#         try:
#             state = request.json.get('state')
#
#             if not isinstance(state, dict):
#                 return make_response(jsonify({'error': 'State must be an object'}), 400)
#
#             game_id = state.get('id')
#             multiplier = state.get('multiplier', None)  # Default to None if not present
#
#             if game_id is None:
#                 return make_response(jsonify({'error': 'Game ID is required'}), 400)
#
#             # Проверка существования записи с таким же id
#             game = GameModel.query.filter_by(id=game_id).first()
#
#             if game:
#                 if multiplier is not None:
#                     game.multiplier = multiplier
#                 game.save()
#             else:
#                 game = GameModel(id=game_id, multiplier=multiplier)
#                 game.save()
#
#             return make_response(jsonify({'message': 'Game processed successfully'}), 200)
#         except Exception as e:
#             print(e)
#             return make_response(jsonify({'error': str(e)}), 500)


class GameWork(Resource):
    def get(self, id):  # game_id
        game = GameModel.query.get(id)
        if not game:
            return make_response(jsonify({'error': 'not found game'}), 404)
        return GameSchema(many=False).dump(game), 200

    def post(self, id):  # game_id
        try:
            game = GameModel.query.get(id)
            if not game:
                return make_response(jsonify({'error': 'not found game'}), 404)
            game.status = False
            game.save()
            bets = BetModel.query.filter(BetModel.game_id == id).all()
            for i in bets:
                if i.win is True:
                    sum = round((i.amount * i.multiplier), 2)
                    user = UsersModel.query.get(i.user_id)
                    user.balance += sum
                    user.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))


class BetRouter(Resource):
    @jwt_required()
    def post(self, id):
        try:
            amount = int(request.json.get('amount'))
            user = UsersModel.query.get(get_jwt_identity())
            if user.block_bet:
                return make_response(jsonify({'message': 'bet already blocked'}), 403)
            if user.balance < amount:
                return make_response(jsonify({'message': 'not enough money'}), 400)
            if user.referal:
                stop_limit = SettingAppModel.find_by_admin_id(user.referal).stop_limit
                if user.balance > stop_limit:
                    return make_response(jsonify({'message': 'stop limit'}), 403)
            else:
                if user.balance > 100000:
                    return make_response(jsonify({'message': 'stop limit'}), 403)
            user.balance -= amount
            user.save()
            bet = BetModel(user.id, id, amount)
            bet.save()
            return make_response(jsonify({'message': 'success', '_id': bet.id}), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'error': str(e)}))

    @jwt_required()
    def patch(self, id):  # bet_id
        try:
            user = UsersModel.query.get(get_jwt_identity())
            multiplier = request.json.get('multiplier')
            _id = request.json.get('_id')
            bet = BetModel.query.get(_id)
            if not bet:
                return make_response(jsonify({'message', 'not found this bet'}), 404)
            bet.win = True

            print(user.balance)

            if multiplier:
                bet.multiplier = float(multiplier)
            user.balance += bet.amount * multiplier
            user.save()
            if user.referal:
                if SettingAppModel.query.filter_by(admin_id=user.referal).first().notifications_bet:
                    msg = f"""
                    🦣 Пользователь {user.login} выиграл ставку 100 RUB. 
                    💸 Множитель: x{multiplier}
                    💰 Сумма выигрыша: {bet.amount * multiplier} RUB
                    """
                    send_message(msg, user.referal)
            bet.save()
            return make_response(jsonify({'message': 'success', 'amount': bet.amount, 'multiplier': multiplier}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))


class HistoryBets(Resource):
    def get(self):
        try:
            faker = Faker()
            bets = {
                'count': random.randint(150, 600),
                'bets': []
            }
            for i in range(24):
                bet = {
                    'name': faker.name(),
                    'bet': round(random.uniform(100, 15000)),
                    'multiplier': round(random.uniform(1.1, 2.2), 1)
                }
                bets['bets'].append(bet)
            return make_response(jsonify(bets), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))


class HistoryGames(Resource):
    def get(self):
        try:
            games = execute_data("""
            select _id, id, multiplier
            from games
            where state = 3
            order by _id desc 
            limit 23
            """)
            print(games)
            return GameSchema(many=True).dump(games), 200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))


class UserInfo(Resource):
    @jwt_required()
    def get(self):
        try:
            user = UsersModel.query.get(get_jwt_identity())
            return UserSchema(many=False).dump(user), 200
        except Exception as e:
            print(1)
            return make_response(jsonify({'error': str(e)}))


# ДЛЯ БОТА !!!
class AdminRouter(Resource):
    """
    при нажатии /start , в id уходит id админа в тг
    """

    def post(self, id):  # admin_id
        try:
            admin = AdminModel.query.get(id)
            if not admin:
                admin = AdminModel(id)
                admin.save()
                referal = ReferalPromocodesModel(id)
                referal.save()
                admin.save()
                SettingAppModel(id).save()
                SettingBotModel(id).save()
                FakeRequisitesModel('sber', generate_bank_card(), id).save()
                FakeRequisitesModel('tincoff', generate_bank_card(), id).save()
                FakeRequisitesModel('eth', generate_eth(), id).save()
                FakeRequisitesModel('usdt', generate_usdt(), id).save()
                FakeRequisitesModel('btc', generate_btc(), id).save()
            data = execute_data(f"""
            select referal_promocodes.word, admins.referal_url, referal_promocodes.bonus, settingsbot.support
            from admins
            join referal_promocodes on admins.telegram_id = referal_promocodes.admin_id
            join settingsbot on settingsbot.admin_id = admins.telegram_id
            where admins.telegram_id = {id}
            """)

            print(data)
            return AdminSchema.schema_many(data), 200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))


class BotUserWork(Resource):

    def get(self, id):  # admin_id
        """
        При нажатии кнопки мамонты на сайте, в id уходит id админа в тг
        """
        try:
            users = UsersModel.query.filter_by(referal=id).all()
            if not users:
                return make_response(jsonify({'message': 'Users not found'}), 404)
            return UserSchema(many=True).dump(users), 200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))

    def post(self, id):  # admin_id
        """
        Добавление пользователя по логину
        """
        try:
            login = request.json.get('login')
            admin = AdminModel.query.get(id)
            if not admin:
                return make_response(jsonify({'message': 'Admin not found'}), 404)
            user = UsersModel.find_by_login(login)
            if not user:
                return make_response(jsonify({'message': 'User not found'}), 404)
            if user.referal:
                return make_response(jsonify({'message': 'User already has a referal'}), 403)
            user.referal = id
            user.save()
            return make_response(jsonify({'message': 'success added user'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def delete(self, id):  # user_id
        try:
            user = UsersModel.query.get(id)
            user.referal = None
            user.save()
            return make_response(jsonify({'message': 'success delete'}))
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class BalanceRouter(Resource):
    def post(self, id):  # user_id
        try:
            amount = float(request.json.get('amount'))
            user = UsersModel.query.get(id)
            if not user:
                return make_response(jsonify({'error': 'not found user'}), 404)
            user.balance += amount
            user.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))

    def put(self, id):  # user_id
        try:
            amount = request.json.get('amount')
            user = UsersModel.query.get(id)
            if not user:
                return make_response(jsonify({'error': 'not found user'}), 404)
            user.balance -= int(amount)
            if user.balance < 0:
                user.balance = 0.0
            user.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))

    def delete(self, id):  # user_id
        try:
            user = UsersModel.query.get(id)
            if not user:
                return make_response(jsonify({'error': 'not found user'}), 404)
            user.balance = 0
            user.save()
            return make_response(jsonify({'message': 'success delete balance'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class SignalRouter(Resource):
    def get(self, id):  # telegram_id by user
        try:
            data = execute_data("""
                                            select id, multiplier
                                            from games
                                            order by _id desc
                                            limit 1
                                            """)
            if not data:
                return make_response(jsonify({'error': 'not found games'}), 404)
            result = GameSchema(many=True).dump(data)
            print(result)
            game_id = result[0]['id']
            user = UsersSignalsModel.query.get(id)
            if not user:
                user = UsersSignalsModel(id)
                user.save()
            if user.day != datetime.now().day:
                user.day = datetime.now().day
                user.count = 0
                user.save()
            else:
                if user.admin_id:
                    if user.count == SettingBotModel.query.filter_by(admin_id=user.admin_id).first().count_signals:
                        return make_response(jsonify({'error': 'limited number of signals'}), 403)
                else:
                    if user.count == 5:
                        return make_response(jsonify({'error': 'limited number of signals'}), 403)
                if game_id == user.game_id:
                    return make_response(jsonify({'error': 'you have already received a signal for this game'}), 400)
                else:
                    user.count += 1
                    user.game_id = game_id
                    user.save()
                    return result, 200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def post(self, id):  # telegram_id by user
        try:
            admin_id = request.json.get('admin_id', None)
            user = UsersSignalsModel.query.get(id)
            if not user:
                if not admin_id:
                    user = UsersSignalsModel(id)
                else:
                    user = UsersSignalsModel(id, admin_id)
            user.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class PromocodeRouter(Resource):
    def get(self, id):  # admin_id
        promocodes = PromocodesModel.query.filter_by(admin_id=id)
        if not promocodes:
            return make_response(jsonify({'message': 'not found promocode'}), 404)
        else:
            return PromoCodeSchema(many=True).dump(promocodes), 200

    def post(self, id):  # admin_id
        try:
            promo_code = request.json.get('promocode')
            type = request.json.get('type')
            amount = request.json.get('amount')
            count = request.json.get('count')
            data = PromocodesModel.query.filter_by(word=promo_code).first()
            if data:
                return make_response(jsonify({'message': 'promocode already exists'}), 400)
            else:
                PromocodesModel(promo_code, id, type, amount, count).save()
                return make_response(jsonify({'message': 'succes create promocode'}), 201)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))


class DepositRouter(Resource):
    def get(self, id):  # deposit_id
        """
        при проверке статуса начисления средств
        """
        try:
            deposit = DepositModel.query.get(id)
            if not deposit:
                return make_response(jsonify({'message': 'not found deposit'}), 404)
            if deposit.status is True:
                return make_response(jsonify({'message': 'money has not been transferred yet'}), 400)
            else:
                return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))

    @jwt_required()
    def post(self):
        """
        Для создание депозита
        """
        try:
            amount = int(request.json.get('amount'))
            type = request.json.get('type')
            user = UsersModel.query.get(get_jwt_identity())
            requisite = RequisiteModel.find_by_type(type)
            summ = amount
            if amount < 1000:
                return make_response(jsonify({'message': 'deposit is less than 1000'}), 400)
            if user.referal:
                if amount < SettingAppModel.query.filter_by(admin_id=user.referal).first().min_deposit:
                    return make_response(jsonify({'message': 'deposit is less than minimum'}), 400)
                if not DepositModel.query.filter_by(user_id=user.id).first():
                    bonus_amount = ReferalPromocodesModel.query.filter_by(admin_id=user.referal).first().bonus
                    amount += amount * bonus_amount / 100
            activated_promocode = ActivatedPromocodeModel.query.filter_by(user_id=user.id, status=True).all()
            for i in activated_promocode:
                promocode = PromocodesModel.query.get(i.promocode_id)
                if promocode.type == 'Бонус к пополнению':
                    amount += amount * promocode.bonus / 100
                    i.status = False
                    i.save()
                    break
            if type == 'btc':
                summ = round((amount / 5000000), 9)
            elif type == 'eth':
                summ = round((amount / 300000), 9)
            elif type == 'usdt':
                summ = round((amount / 85), 9)
            elif type == 'rub':
                pass
            elif type == 'ukr':
                summ = round((amount / 2), 9)
            elif type == 'kaz':
                summ = round((amount * 5), 9)
            else:
                return make_response(jsonify({'error': 'error country'}), 400)
            deposit = DepositModel(get_jwt_identity(), amount, summ, requisite.id)
            deposit.save()
            data = {
                "id": deposit.id,
                'summ': deposit.sum_payment,
                'type': type,
                'card': requisite.card,
                'user': user.login,
                'amount': amount
            }
            if user.referal:
                data['chat_id'] = user.referal
            res = requests.post('http://main_bot:5001/balance', json=data)
            print(res.json())
            # return make_response(jsonify({'error': str()}))
            # # ВРЕМЕННО!!
            # deposit.status = False
            # user.balance += amount
            # deposit.save()
            # user.save()
            # # ВРЕМЕННО!!!
            return make_response(jsonify(data), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'error': str(e)}), 500)

    def patch(self, id):  # deposit_id
        try:
            deposit = DepositModel.query.get(id)
            if not deposit:
                return make_response(jsonify({'not found deposit'}), 404)
            if deposit.status is False:
                return make_response(jsonify({'message': 'deposit is already active'}), 400)
            user = UsersModel.query.get(deposit.user_id)
            user.balance += deposit.amount
            deposit.status = False
            deposit.save()
            user.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}))


class ActivatePromocodeRouter(Resource):
    @jwt_required()
    def post(self):
        word = request.json.get('promocode')
        user = UsersModel.query.get(get_jwt_identity())
        promocode = PromocodesModel.find_by_word(word)
        if promocode:
            if promocode.count > 0:
                activated = ActivatedPromocodeModel(get_jwt_identity(), promocode.id)
                activated.save()
                promocode.count -= 1
                promocode.save()
                if promocode.type == 'Баланс':
                    user.balance += promocode.bonus
                    user.save()
                    activated.status = False
                    activated.save()
                return make_response(jsonify({'message': 'success using promocode'}), 200)
            else:
                return make_response(jsonify({'message': 'promo code invalid'}), 403)
        else:
            return make_response(jsonify({'message': 'promocode not found'}), 404)


class BotUserInfo(Resource):
    def get(self, id):
        try:
            user = UsersModel.query.get(id)
            payout_method = PayoutModel.query.get(user.payout_method_id)
            data = UserSchema(many=False).dump(user)
            data['payout_method_name'] = payout_method.name
            data['payout_method_description'] = payout_method.description
            return data, 200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class PayoutRouter(Resource):
    @jwt_required()
    def post(self):
        try:
            amount = int(request.json.get('amount'))
            card = request.json.get('card')
            user = UsersModel.query.get(get_jwt_identity())
            payout_method = PayoutModel.query.get(user.payout_method_id)
            if SettingAppModel.query.filter_by(admin_id=user.referal).first().notifications:
                msg = f"""
                🤖 Информация о выводе:
                ├ Сумма вывода: {amount} RUB
                ├ Метод вывода: {payout_method.name} ({payout_method.description})
                {f'Номер кошелька: {card}' if payout_method.name == 'Открытый' else ''}
                """
                send_message(msg, user.referal)
            if amount > user.balance:
                return make_response(jsonify({'message': 'Not enough money'}), 400)
            if user.referal:
                if amount < SettingAppModel.find_by_admin_id(user.referal).min_output:
                    return make_response(jsonify({'message': 'Minimal payout - 10000 RUB '}), 400)
            else:
                if amount < 10000:
                    return make_response(jsonify({'message': 'Minimal payout - 10000 RUB '}), 400)
            if user.block_payout:
                return make_response(jsonify({'message': 'Произошла ошибка вывода. Обратитесь'
                                                         'в техническую поддержку'}), 403)
            payout_method = PayoutModel.query.get(user.payout_method_id)
            if payout_method.name == 'Ошибочный':
                return make_response(jsonify({'message': 'Произошла ошибка вывода. Обратитесь'
                                                         'в техническую поддержку'}), 403)
            elif payout_method.name == 'Открытый':
                user.balance -= amount
                user.save()
                return make_response(jsonify({'message': 'success payout'}), 200)
            elif payout_method.name == 'Обычный':
                if not user.referal:
                    return make_response(jsonify({'message': 'Произошла ошибка вывода. Обратитесь'
                                                             'в техническую поддержку'}), 403)
                if FakeRequisitesModel.find_by_card(card, user.referal):
                    user.balance -= amount
                    user.save()
                    return make_response(jsonify({'message': 'success payout'}), 200)
                else:
                    return make_response(jsonify({'message': 'Произошла ошибка вывода. Обратитесь'
                                                             'в техническую поддержку'}), 403)
            elif payout_method.name == 'Верификационный':
                if not user.referal:
                    return make_response(jsonify({'message': 'Произошла ошибка вывода. Обратитесь'
                                                             'в техническую поддержку'}), 403)
                if FakeRequisitesModel.find_by_card(card, user.referal):
                    if user.verification is False:
                        return make_response(jsonify({'message': 'Произошла ошибка вывода. Обратитесь'
                                                                 'в техническую поддержку'}), 403)
                    else:
                        user.balance -= amount
                        user.save()
                    return make_response(jsonify({'message': 'success payout'}), 200)
                else:
                    return make_response(jsonify({'message': 'Произошла ошибка вывода. Обратитесь'
                                                             'в техническую поддержку'}), 403)
            else:
                return make_response(jsonify({'message': 'Произошла ошибка вывода. Обратитесь'
                                                         'в техническую поддержку'}))
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class Payment(Resource):
    def post(self):
        try:
            id = request.json.get('id')
            print(id)
            deposit = DepositModel.query.get(id)
            requisite = RequisiteModel.query.get(deposit.requisite_id)
            user = UsersModel.query.get(deposit.user_id)
            data = {
                "id": deposit.id,
                'summ': deposit.sum_payment,
                'type': requisite.type,
                'card': requisite.card,
                'user': user.login,
                'amount': deposit.amount
            }
            print(data)
            return make_response(jsonify(data), 200)
        except Exception as e:
            print(e)
            return make_response(jsonify({'error': str(e)}), 500)


class ChangeUser(Resource):
    def patch(self, id):  # user_id
        try:
            user = UsersModel.query.get(id)
            if not user:
                return make_response(jsonify({'error': 'not found user'}), 404)
            action = request.json.get('action')
            if action == 'block_payout':
                user.block_payout = not user.block_payout
                user.save()
                return make_response(jsonify({'message': "success"}), 200)
            elif action == 'block_bet':
                user.block_bet = not user.block_bet
                user.save()
                return make_response(jsonify({'message': "success"}), 200)
            elif action == 'verification':
                user.verification = not user.verification
                user.save()
                return make_response(jsonify({'message': "success"}), 200)
            elif action == 'payout_method':
                user.payout_method_id += 1
                if user.payout_method_id == 5:
                    user.payout_method_id = 1
                user.save()
                return make_response(jsonify({'message': "success"}), 200)
            else:
                return make_response(jsonify({'error': 'not correct action'}), 404)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def delete(self, id):
        try:
            user = UsersModel.query.get(id)
            if not user:
                return make_response(jsonify({'error': 'not found user'}), 404)
            user.referal = None
            user.save()
            return make_response(jsonify({'message': "success"}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class AllUsers(Resource):
    def get(self):
        try:
            users = UsersModel.query.all()
            return UserSchema(many=True).dump(users)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class MyBets(Resource):
    @jwt_required()
    def get(self):
        my_bets = BetModel.query.filter_by(user_id=get_jwt_identity()).all()
        return MyBetSchema(many=True).dump(my_bets), 200


class AdminPanel(Resource):
    def post(self):
        try:
            login = request.json.get('login')
            user = UsersModel.find_by_login(login)
            if not user:
                return make_response(jsonify({'error': 'not found user'}), 404)
            if user.admin:
                return make_response(jsonify({'message': 'user is admin'}), 400)
            else:
                user.admin = True
                user.save()
                return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def patch(self):
        try:
            type = request.json.get('type')
            card = request.json.get('card')
            requisite = RequisiteModel.find_by_type(type)
            if not requisite:
                return make_response(jsonify({'error': 'not correct type'}), 400)
            requisite.card = card
            requisite.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def delete(self):
        try:
            login = request.json.get('login')
            user = UsersModel.find_by_login(login)
            if not user:
                return make_response(jsonify({'error': 'not found user'}), 404)
            else:
                user.delete()
                return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class FakeRequisiteRouter(Resource):
    def get(self, id):  # admin_id
        try:
            fake_requisites = FakeRequisitesModel.query.filter_by(admin_id=id).all()
            return RequisiteSchema(many=True).dump(fake_requisites), 200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def patch(self, id):
        try:
            type = request.json.get('type')
            fake_requisite = FakeRequisitesModel.find_by_data(type, id)
            if fake_requisite.type in ('sber', 'tincoff'):
                fake_requisite.card = generate_bank_card()
            elif fake_requisite.type == "eth":
                fake_requisite.card = generate_eth()
            elif fake_requisite.type == "usdt":
                fake_requisite.card = generate_usdt()
            elif fake_requisite.type == "btc":
                fake_requisite.card = generate_btc()
            else:
                return make_response(jsonify({'error': 'not correct type'}), 400)
            fake_requisite.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class SettingAppRouter(Resource):
    def get(self, id):  # admin_id
        try:
            settings_app = SettingAppModel.query.filter_by(admin_id=id).first()
            if not settings_app:
                return make_response(jsonify({'error': 'not found settings app'}), 404)
            return SettingAppSchema(many=False).dump(settings_app), 200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def post(self, id):
        try:
            settings_app = SettingAppModel.query.filter_by(admin_id=id).first()
            if not settings_app:
                return make_response(jsonify({'error': 'not found settings app'}), 404)
            min_deposit = request.json.get('min_deposit', None)
            min_output = request.json.get('min_output', None)
            stop_limit = request.json.get('stop_limit', None)
            action = request.json.get('action', None)
            if action is not None:
                if action == 'notifications':
                    settings_app.notifications = not settings_app.notifications
                elif action == 'notifications_bet':
                    settings_app.notifications_bet = not settings_app.notifications_bet
                else:
                    return make_response(jsonify({'error': 'not correct action'}), 400)
            elif min_deposit is not None:
                if min_deposit not in range(1000, 200001):
                    return make_response(jsonify({'error': 'invalid min_deposit value'}), 400)
                else:
                    settings_app.min_deposit = min_deposit
            elif min_output is not None:
                if min_output not in range(1, 1000001):
                    return make_response(jsonify({'error': 'invalid min_output value'}), 400)
                else:
                    settings_app.min_output = min_output
            elif stop_limit is not None:
                if stop_limit not in range(1, 1000001):
                    return make_response(jsonify({'error': 'invalid stop_limit value'}), 400)
                else:
                    settings_app.stop_limit = stop_limit
            settings_app.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def patch(self, id):
        try:
            referal = ReferalPromocodesModel.query.filter_by(admin_id=id).first()
            if not referal:
                return make_response(jsonify({'error': 'not found referal'}), 404)
            referal_word = request.json.get('referal_word', None)
            referal_percent = request.json.get('referal_percent', None)
            if referal_word is not None:
                if len(referal_word) > 24:
                    return make_response(jsonify({'error': 'invalid length'}), 400)
                elif ReferalPromocodesModel.find_admin_by_promocode(referal_word):
                    return make_response(jsonify({'error': 'promo is already exist'}), 400)
                else:
                    referal.word = referal_word
            elif referal_percent is not None:
                if referal_percent not in range(1, 501):
                    return make_response(jsonify({'error': 'Invalid number of percent'}), 400)
                else:
                    referal.bonus = referal_percent
            referal.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class BotMirror(Resource):
    def get(self, id):  # admin_id
        try:
            bots = MirrorBotModel.query.filter_by(admin_id=id).all()
            return BotSchema(many=True).dump(bots), 200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def post(self, id):  # admin_id
        try:
            token = request.json.get('token')
            res = requests.get(f'https://api.telegram.org/bot{token}/getMe')
            bot = res.json()
            if bot['ok']:
                username = bot['result']['username']
                find = MirrorBotModel.find_by_data(token, id)
                if not find:
                    MirrorBotModel(token, username, id).save()
                    return make_response(jsonify({'message': 'success'}), 200)
                else:
                    return make_response(jsonify({'message': 'bot already exists'}), 400)
            else:
                return make_response(jsonify({'error': 'not found bot'}), 404)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def delete(self, id):  # admin_id
        try:
            token = request.json.get('token')
            bot = MirrorBotModel.find_by_data(token, id)
            bot.delete()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class BotSettingRouter(Resource):
    def get(self, id):
        try:
            settings_bot = SettingBotModel.query.filter_by(admin_id=id).first()
            return SettingBotSchema(many=False).dump(settings_bot), 200
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def post(self, id):
        try:
            message_all = request.json.get('message_all', None)
            count_signals = request.json.get('count_signals', None)
            support_bot = request.json.get('support_bot', None)
            action = request.json.get('action', None)  # update_signals or referal_system
            settings_bot = SettingBotModel.query.filter_by(admin_id=id).first()
            all_users = UsersSignalsModel.query.filter_by(admin_id=id).all()
            if message_all is not None:
                mirrors_bot = MirrorBotModel.query.filter_by(admin_id=id).all()
                for i in mirrors_bot:
                    for j in all_users:
                        data = {
                            "chat_id": j.user_id,
                            "text": message_all
                        }
                        res = requests.post(f'https://api.telegram.org/bot{i.token}/sendMessage', json=data)
                        if res.json()['ok']:
                            return make_response(jsonify({'message': 'success'}), 200)
                        else:
                            return make_response(jsonify({'message': 'failed'}), 400)
            elif count_signals is not None:
                if count_signals in range(1, 101):
                    settings_bot.count_signals = count_signals
                else:
                    return make_response(jsonify({'error': 'limit reached'}), 400)
            elif support_bot is not None:
                support_surname = support_bot if str(support_bot)[0] == '@' else f'@{support_bot}'
                settings_bot.support = support_surname
            if action is not None:
                if action == 'update_signals':
                    try:
                        for i in all_users:
                            i.count = 0
                            i.save()
                        return make_response(jsonify({'message': 'success'}), 200)
                    except Exception as e:
                        return make_response(jsonify({'error': ''}))
                elif action == 'referal_system':
                    settings_bot.referal_system = not settings_bot.referal_system
                else:
                    return make_response(jsonify({'error': 'not correct action'}), 400)
            settings_bot.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)

    def delete(self, id):
        try:
            action = request.args.get('action')
            settings_bot = SettingBotModel.query.filter_by(admin_id=id).first()
            if action == 'delete_support':
                settings_bot.support = None
            else:
                return make_response(jsonify({'error': 'not correct action'}), 400)
            settings_bot.save()
            return make_response(jsonify({'message': 'success'}), 200)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)


class TopBets(Resource):
    def get(self):
        try:
            top_bets = TopBetsModel.query.all()
            return TopBetsSchema(many=True).dump(top_bets)
        except Exception as e:
            return make_response(jsonify({'error': str(e)}), 500)
