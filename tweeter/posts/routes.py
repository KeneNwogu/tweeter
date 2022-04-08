# likes and bookmarks

from datetime import datetime
from flask import Blueprint, request
from bson import json_util, ObjectId
from tweeter import mongo
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import resource_not_found
from tweeter.utitlities import upload_files, validate_id

posts = Blueprint('posts', __name__)


@posts.route('/<post_id>/like')
@login_required
def like_post(post_id):
    user = get_current_user()
    if not mongo.db.likes.find_one({'post': ObjectId(post_id), 'user': user.get('_id')}):
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
            "$inc": {
                "likes": 1
            }
        })
        mongo.db.likes.insert_one({'post': ObjectId(post_id), 'user': user.get('_id')})
        return {
            'message': 'success',
            'liked': True,
            'likes': mongo.db.posts.find_one({'_id': ObjectId(post_id)}).get('likes')
        }

    else:
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
            "$inc": {
                "likes": -1
            }
        })
        mongo.db.likes.delete_one({'post': ObjectId(post_id), 'user': user.get('_id')})
        return {
            'message': 'success',
            'liked': False,
            'likes': mongo.db.posts.find_one({'_id': ObjectId(post_id)}).get('likes')
        }


@posts.route('/<post_id>/bookmark')
@login_required
def bookmark_post(post_id):
    post_id = validate_id(post_id)
    user = get_current_user()
    if post_id not in mongo.db.users.find_one({'_id': user.get('_id')}).get('bookmarks', []):
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
            "$inc": {
                "bookmarks": 1
            }
        })
        mongo.db.users.update_one({'_id': user.get('_id')}, {
            '$addToSet': {
                'bookmarks': ObjectId(post_id)
            }
        })
        return {
            'message': 'success'
        }
    else:
        return {
            'message': 'success',
            'info': 'This post is already bookmarked'
        }
