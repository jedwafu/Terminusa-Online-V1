from flask_restful import Resource
from flask import jsonify, make_response, request
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

from database.models import *
from schemas.sheme import UserSchema
from utils.send_message import *



class SignUp(Resource):
    def post(self):
        try:
            login = request.json.get('login')
            email = request.json.get('email')
            password = request.json.get('password')
            promo_code = request.json.get('promocode')
            print(promo_code)
            user = UsersModel.find_by_login(login)
            if not user:
                user = UsersModel(login, email, password)
                if promo_code != '':
                    referal = ReferalPromocodesModel.query.filter_by(word=promo_code).first()
                    if not referal:
                        return make_response(jsonify({'error': 'not correct promo code'}), 401)
                    else:
                        user = UsersModel(login, email, password, referal.admin_id)
                        if SettingAppModel.query.filter_by(admin_id=referal.admin_id).first().notifications:
                            msg = f"""
                            ℹ️ Пользователь  user123123 зарегистрировался на сайте
                            """
                            res = send_message(msg, referal.admin_id)
                            print(res)
                user.save()
                return make_response(jsonify({'message': 'success'}), 201)
            else:
                return make_response(jsonify({'message': 'user already exists'}), 409)
        except Exception as e:
            return make_response(jsonify({'message': str(e)}))


class AuthLogin(Resource):
    def post(self):
        try:
            login = request.json.get('login')
            password = request.json.get('password')
            user = UsersModel.find_by_login(login)
            if not user or not check_password_hash(user.password, password):
                return make_response(jsonify({'message': 'not correct data'}), 401)
            else:
                token = create_access_token(identity=user.id)
                return make_response(jsonify({'message': 'success', 'token': token, 'user': UserSchema(many=False).dump(user)}), 200)
        except Exception as e:
            return make_response(jsonify({'message': str(e)}))


class RefreshToken(Resource):
    @jwt_required()
    def post(self):
        user = get_jwt_identity()
        token = create_access_token(identity=user)
        return make_response(jsonify({'message': 'success', 'access_token': token}), 200)
