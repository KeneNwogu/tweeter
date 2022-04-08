from pprint import pprint

from bson import json_util, ObjectId
from cloudinary.uploader import upload
from flask import Blueprint, request
from werkzeug.security import generate_password_hash

from tweeter import mongo, app
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import resource_not_found, unauthorised, bad_request
from tweeter.utitlities import valid_email, gravatar_profile_image, create_register_jwt, validate_id

users = Blueprint('users', __name__)


@users.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        data = request.get_json(force=True)
        if 'email' not in data:
            return bad_request("Invalid request format")

        if mongo.db.users.find_one({"email": data['email']}):
            return bad_request('please use a different email address')

        if not valid_email(data['email']):
            return bad_request('An invalid email was provided')

        password_hash = generate_password_hash(data['password'])
        # TODO gravitar profile image
        email = data['email']
        profile_image = gravatar_profile_image(email)
        user_data = {
            "email": email,
            "username": email,
            "password_hash": password_hash,
            "profile_image": profile_image,
            "bio": "Hey there! I'm using Tweeter",
            "followers": 0,
            "following": 0
        }
        user = mongo.db.users.insert_one(user_data)

        token = create_register_jwt(user.inserted_id, app.config['SECRET_KEY'])
        return {
            "message": "successfully registered user",
            "token": token,
            "email": user_data.get('email'),
            "username": user_data.get('username'),
            "bio": user_data.get('bio'),
            "profile_image": user_data.get('profile_image')
        }


@users.route('/<user_id>/profile', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    user_in_session = get_current_user()
    user_id = validate_id(user_id)
    user = mongo.db.users.find_one({'_id': user_id})
    if user is None:
        resource_not_found('This user has has been deleted or deactivated')
    if request.method == 'GET':
        data = {
            "_id": str(user.get('_id')),
            "username": user.get('username'),
            "email": user.get('email'),
            "bio": user.get('bio'),
            "followers": len(list(mongo.db.followers.find({'user': ObjectId(user_id)}))),
            "following": len(list(mongo.db.followers.find({'follower': ObjectId(user_id)}))),
            "profile_image": user.get('profile_image')
        }
        if str(user_in_session.get('_id')) == str(user.get('_id')):
            data['self'] = True
            data['follows_you'] = False
            data['you_follow'] = False
        else:
            data['self'] = False
            data['you_follow'] = True if mongo.db.followers.find_one({
                'user': ObjectId(user.get('_id')),
                'follower': ObjectId(user_in_session.get('_id'))
            }) else False
            data['follows_you'] = True if mongo.db.followers.find_one({
                'user': ObjectId(user_in_session.get('_id')),
                'follower': ObjectId(user.get('_id'))
            }) else False
        return json_util.dumps(data)

    if request.method == 'POST':
        if str(user_in_session.get('_id')) != str(user.get('_id')):
            return unauthorised('you are not allowed to update this user.')
        fields = ['username', 'bio', 'email']
        form = request.form
        profile_image = request.files.get('profile_image')
        data = {}

        if 'email' in form:
            email = form.get('email')
            if not valid_email(email):
                return bad_request('Invalid email was provided')

        if not (form or profile_image) or (not form and profile_image.filename == ''):
            return bad_request('No data was provided')

        else:
            for field in fields:
                if form.get(field):
                    data[field] = form.get(field)
            if profile_image:
                if profile_image.filename != '':
                    new_profile_image = upload(profile_image).get('url')
                    data['profile_image'] = new_profile_image

            mongo.db.users.update_one({'_id': user.get('_id')}, {"$set": data})
            updated_user = mongo.db.users.find_one({'_id': user.get('_id')})
            return {
                "message": "successfully updated details",
                "username": updated_user.get('username'),
                "email": updated_user.get('email'),
                "bio": updated_user.get('bio'),
                "profile_image": updated_user.get('profile_image'),
            }


@users.route('/<user_id>/follow')
@login_required
def follow_user(user_id):
    user = get_current_user().get('_id')
    if not mongo.db.followers.find_one({'follower': user, 'user': ObjectId(user_id)}):
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {
            "$inc": {
                "followers": 1
            }
        })
        mongo.db.followers.insert_one({'user': ObjectId(user_id), 'follower': user})
        return {
            "message": "success",
            "followers": len(list(mongo.db.followers.find({'user': ObjectId(user_id)}))),
            "following": True
        }
    else:
        if not mongo.db.users.find_one({'_id': ObjectId(user_id)}):
            return resource_not_found('user does not exist')
        else:
            return {
                "message": "you are already following this user",
                "followers": len(list(mongo.db.followers.find({'user': ObjectId(user_id)}))),
                "following": True
            }


@users.route('/<user_id>/unfollow')
@login_required
def unfollow_user(user_id):
    user = get_current_user().get('_id')
    if mongo.db.followers.find_one({'user': user, 'follower': ObjectId(user_id)}):
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {
            "$inc": {
                "followers": -1
            }
        })
        mongo.db.followers.delete_one({'user': ObjectId(user_id), 'follower': user})
        return {
            "message": "success"
        }
    else:
        return {
            "message": "unfollowed"
        }


@users.route('/<user_id>/followers')
def user_followers(user_id):
    # return users following the user_id
    pipeline = [
        {
            "$match": {"user": ObjectId(user_id)}
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "follower",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"}
    ]
    followers = mongo.db.followers.aggregate(pipeline)
    return json_util.dumps(followers)


@users.route('/<user_id>/following')
def user_following(user_id):
    # return users following the user_id
    pipeline = [
        {
            "$match": {"follower": ObjectId(user_id)}
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"}
    ]
    following = mongo.db.followers.aggregate(pipeline)
    return json_util.dumps(following)


@users.route('/bookmarks')
@login_required
def user_bookmarks():
    current_user_id = get_current_user().get('_id')
    # aggregation
    pipeline = [
        {
            "$match": {"_id": ObjectId(current_user_id)}
        },
        {
            "$lookup": {
                "from": "posts",
                "localField": "bookmarks",
                "foreignField": "_id",
                "as": "bookmarks"
            }
        },
        {"$unwind": "$bookmarks"},
        {
            "$lookup": {
                "from": "users",
                "localField": "bookmarks.user",
                "foreignField": "_id",
                "as": "bookmarks.user"
            }
        },
        {"$unwind": "$bookmarks"},
        {
            "$project": {
                "bookmarks.user.bookmarks": 0
            }
        }
    ]
    bookmarks = list(mongo.db.users.aggregate(pipeline))
    return json_util.dumps(bookmarks)
