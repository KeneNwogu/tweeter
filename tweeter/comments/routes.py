from datetime import datetime
from flask import Blueprint, request
from bson import json_util, ObjectId
from tweeter import mongo
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import resource_not_found
from tweeter.utitlities import upload_files, validate_id

comments = Blueprint('comments', __name__)


@comments.route('/<post_id>/comments', methods=['GET', 'POST'])
@login_required
def comment(post_id):
    pipeline = [
        {
            "$match": {"post": ObjectId(post_id)}
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
    post_pipeline = [
        {
            "$match": {"_id": ObjectId(post_id)}
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
    if request.method == 'GET':
        current_user = get_current_user()
        current_user_id = current_user.get('_id')
        user_bookmarks = current_user.get('bookmarks', [])
        user_likes = list(mongo.db.likes.find({'user': current_user_id}))
        liked_posts = list(map(lambda x: x.get('post'), user_likes))

        post = list(mongo.db.posts.aggregate(post_pipeline))[0]

        retweeted_by = post.get('retweeted_by', [])  # user ids

        post['liked'] = True if post.get('_id') in liked_posts else False
        post['saved'] = True if post.get('_id') in user_bookmarks else False
        post['retweeted'] = True if current_user_id in retweeted_by else False

        comments_response = mongo.db.comments.aggregate(pipeline)
        response = {
            "post": post,
            "comments": comments_response
        }
        return json_util.dumps(response)

    if request.method == 'POST':
        user = get_current_user()
        form = request.form
        files = request.files.getlist('file')
        post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
        if post:
            mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {
                "$inc": {
                    "comments": 1
                }
            })
            post_urls = upload_files(files)
            data = {
                'post': ObjectId(post_id),
                'caption': form.get('caption'),
                'images': post_urls,
                'comments': 0,
                'retweets': 0,
                'likes': 0,
                'saves': 0,
                'user': user.get('_id'),
                'createdAt': datetime.utcnow()
            }
            mongo.db.comments.insert_one(data)
            comments_response = mongo.db.comments.aggregate(pipeline)
            return json_util.dumps({
                "message": "successfully commented",
                'comments': comments_response
            })
        else:
            # 404 message
            return resource_not_found('Post has been deleted or not found')


@comments.route('/comment/<comment_id>/like', methods=['GET'])
@login_required
def like_comment(comment_id):
    user_id = get_current_user().get('_id')
    comment_id = validate_id(comment_id)
    if not mongo.db.comments.find_one({'_id': comment_id}):
        return resource_not_found('This comment is unavailable')
    if not mongo.db.likes.find_one({'comment': comment_id, 'user': user_id, 'is_comment': True}):
        mongo.db.comments.update_one({'_id': ObjectId(comment_id)}, {
            "$inc": {
                "likes": 1
            }
        })
        mongo.db.likes.insert_one({'comment': ObjectId(comment_id), 'user': user_id, 'is_comment': True})
        return {
            'message': 'success',
            'liked': True,
            'likes': mongo.db.comments.find_one({'_id': comment_id}).get('likes')
        }
    else:
        mongo.db.comments.update_one({'_id': comment_id}, {
            "$inc": {
                "likes": -1
            }
        })
        mongo.db.likes.delete_one({'comment': ObjectId(comment_id), 'user': user_id})
        return {
            'message': 'success',
            'liked': False,
            'likes': mongo.db.comments.find_one({'_id': ObjectId(comment_id)}).get('likes')
        }