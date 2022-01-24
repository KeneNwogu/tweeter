from functools import wraps

import jwt
from bson import ObjectId
from flask import request
from flask_httpauth import HTTPTokenAuth

from tweeter import app, mongo
from tweeter.api.errors import error_response, bad_request

token_auth = HTTPTokenAuth()


def get_current_user():
    jwt_cookie = request.headers.get('Authorization')
    if jwt_cookie:
        try:
            user_payload = jwt.decode(jwt_cookie, app.config['SECRET_KEY'], 'HS256')
        except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.ExpiredSignatureError) as e:
            return None
        else:
            return mongo.db.users.find_one({'_id': ObjectId(user_payload['user_id'])})


def login_required(f):
    @wraps(f)
    def check_user_is_logged(*args, **kwargs):
        jwt_cookie = request.headers.get('Authorization')
        if jwt_cookie:
            try:
                jwt.decode(jwt_cookie, app.config['SECRET_KEY'], 'HS256')
            except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.ExpiredSignatureError) as e:
                return bad_request("Unauthorized")
            else:
                return f(*args, **kwargs)
        else:
            return bad_request("Unauthorized. No jwt cookie found")
    return check_user_is_logged


@token_auth.error_handler
def token_auth_error(status):
    return error_response(status)
