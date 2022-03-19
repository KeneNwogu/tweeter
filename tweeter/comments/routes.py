from flask import Blueprint, request
from bson import json_util, ObjectId
from tweeter import mongo
from tweeter.api.auth import login_required
from tweeter.api.errors import resource_not_found
from tweeter.utitlities import upload_files

comments = Blueprint('comments', __name__)


@comments.route('/<post_id>/comments')
@login_required
def comment(post_id):
    if request.method == 'GET':
        comments_response = mongo.db.comments.find({'post': ObjectId(post_id)})
        return json_util.dumps(list(comments_response))

    if request.method == 'POST':
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
            mongo.db.comments.insert_one({
                'post': ObjectId(post_id),
                'caption': form.get('caption'),
                'images': post_urls,
                'comments': 0,
                'retweets': 0,
                'likes': 0
            })
            return {
                "message": "successfully commented",
            }
        else:
            # 404 message
            return resource_not_found('Post has been deleted or not found')
