# likes and bookmarks

from datetime import datetime
from flask import Blueprint, request
from bson import json_util, ObjectId
from tweeter import mongo
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import resource_not_found
from tweeter.utitlities import upload_files, validate_id
from tweeter.utitlities.pipelines import post_likes_aggregation_pipeline

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
        mongo.db.likes.insert_one({'post': ObjectId(post_id), 'user': user.get('_id'), 'is_comment': False})
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
                "saves": 1
            }
        })
        mongo.db.users.update_one({'_id': user.get('_id')}, {
            '$addToSet': {
                'bookmarks': ObjectId(post_id)
            }
        })
        return {
            'message': 'success',
            'bookmarked': True
        }
    else:
        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
            "$inc": {
                "saves": -1
            }
        })
        mongo.db.users.update_one({'_id': user.get('_id')}, {
            '$pull': {
                'bookmarks': ObjectId(post_id)
            }
        })
        return {
            'message': 'success',
            'bookmarked': False
        }


@posts.route('/<post_id>/retweet')
@login_required
def retweet_post(post_id):
    post_id = validate_id(post_id)
    post = mongo.db.posts.find_one({'_id': post_id})
    if post:
        user = get_current_user()
        retweeted_by = post.get('retweeted_by', [])
        if user not in retweeted_by:
            mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
                "$inc": {
                    "retweets": 1
                },
                '$addToSet': {
                    'retweeted_by': user
                }
            })
            return {
                'message': 'success',
                'retweeted': True
            }
        else:
            mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
                "$inc": {
                    "retweets": -1
                },
                '$pull': {
                    'retweeted_by': user
                }
            })
            return {
                'message': 'success',
                'retweeted': False
            }
    else:
        return resource_not_found('Cannot retrieve details of this post')


@posts.route('/post/<post_id>/likes')
def post_likes(post_id):
    post_id = validate_id(post_id)
    pipeline = post_likes_aggregation_pipeline(post_id)
    response = list(mongo.db.likes.aggregate(pipeline))
    return json_util.dumps(response)
