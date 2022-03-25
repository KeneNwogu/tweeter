from datetime import datetime
from flask import Blueprint, request
from bson import json_util, ObjectId
from tweeter import mongo
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import resource_not_found
from tweeter.utitlities import upload_files

comments = Blueprint('comments', __name__)


@comments.route('/<post_id>/comments')
@login_required
def comment(post_id):
    if request.method == 'GET':
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
        comments_response = mongo.db.comments.aggregate(pipeline)
        response = {
            "post": mongo.db.posts.find_one({'_id': ObjectId(post_id)}),
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
                    "comments"
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
                'user': user.get('_id'),
                'createdAt': datetime.utcnow()
            }
            mongo.db.comments.insert_one(data)
            return {
                "message": "successfully commented",
                'comment': data
            }
        else:
            # 404 message
            return resource_not_found('Post has been deleted or not found')
