from datetime import datetime
from flask import Blueprint, request
from bson import json_util, ObjectId
from tweeter import mongo
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import resource_not_found
from tweeter.utitlities import upload_files


users = Blueprint('users', __name__)


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
            "message": "success"
        }
    else:
        if not mongo.db.users.find_one({'_id': ObjectId(user_id)}):
            return resource_not_found('user does not exist')


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

