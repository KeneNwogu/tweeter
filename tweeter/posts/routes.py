# likes and bookmarks

from datetime import datetime
from flask import Blueprint, request
from bson import json_util, ObjectId
from tweeter import mongo
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import resource_not_found
from tweeter.utitlities import upload_files


posts = Blueprint('posts', __name__)


@posts.route('/<post_id>/like')
@login_required
def like_post(post_id):
    user = get_current_user()
    if not mongo.db.likes.find_one({'post': ObjectId(post_id), 'user': user.get('_id')}):
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
            "$inc": {
                "likes"
            }
        })
        mongo.db.likes.insert_one({'post': ObjectId(post_id), 'user': user.get('_id')})

    else:
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
            "$inc": {
                "likes": -1
            }
        })
        mongo.db.likes.delete_one({'post': ObjectId(post_id), 'user': user.get('_id')})
    return {
        'message': 'success'
    }


@posts.route('/<post_id>/bookmark')
@login_required
def bookmark_post(post_id):
    user = get_current_user()
    if not mongo.db.bookmarks.find_one({'user': user.get('_id')}):
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
            "$inc": {
                "bookmarks"
            }
        })
        mongo.db.bookmarks.insert_one({'user': user.get('_id'), 'posts': [ObjectId(post_id)]})
    else:
        mongo.db.bookmarks.update_one({'user': user.get('_id')}, {
            '$addToSet': {
                'posts': ObjectId(post_id)
            }
        })
    return {
        'message': 'success'
    }