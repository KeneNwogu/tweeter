import datetime
import os

import jwt
from bson import json_util
from flask import request, make_response
from flask_cors import cross_origin
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from tweeter import app, ALLOWED_EXTENSIONS
from tweeter import mongo
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import bad_request
from tweeter.utitlities import cloudinary_file_upload


@app.route('/login', methods=['POST'])
@cross_origin()
def login():
    if request.method == 'POST':
        data = request.get_json(force=True)
        if 'email' not in data or 'password' not in data:
            return bad_request("Email or username not provided")
        email = data['email']
        password = data['password']
        user = mongo.db.users.find_one({"email": email})
        if user:
            if check_password_hash(user.get('password_hash'), password):
                # perform login
                payload = {
                    "user_id": str(user.get('_id')),
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=35),
                    'iat': datetime.datetime.utcnow()
                }
                # set jwt
                token = jwt.encode(payload, app.config['SECRET_KEY'], "HS256")
                data = {
                    "message": "successfully logged in user",
                    "token": token,
                    "_id": user.get('_id'),
                    "email": user.get('email'),
                    "username": user.get('username'),
                    "bio": user.get('bio'),
                    "profile_image": user.get('profile_image')
                }
                response = make_response(data, 201)
                return response
        return bad_request("Invalid email or password")


@app.route('/posts/create', methods=['POST'])
@login_required
def create_post():
    user = get_current_user()
    form = request.form
    caption = form.get('caption')
    files = request.files.getlist('file')
    restricted = form.get('restricted', False)

    # a file or caption must be provided
    if not (caption or files) or (caption == '' and files == []):
        return bad_request("must provide a caption or image")

    else:
        post_urls = []
        for file in files:
            if file.filename != '':
                # handle file upload and posting
                filename = secure_filename(file.filename)
                _, ext = os.path.splitext(filename)
                if ext not in ALLOWED_EXTENSIONS:
                    return bad_request("file extension not allowed")

                url = cloudinary_file_upload(file)
                post_urls.append(url)
        post = mongo.db.posts.insert_one({"caption": caption, "post_urls": post_urls, "user": user.get('_id'),
                                          "restricted": restricted, 'comments': 0, 'retweets': 0, 'likes': 0,
                                          'createdAt': datetime.datetime.utcnow()
                                          })
        # TODO create socket and broadcast to user's followers
        # TODO replace the use of loops for broadcasting
        followers = mongo.db.followers.find_one({"user_id": user.get('_id')})
        feed_post = mongo.db.posts.find_one({"_id": post.inserted_id})
        if followers:
            for follower in followers:
                # add feed for follower
                mongo.db.feed.insert_one({"user_id": follower.get('_id'), "post": feed_post})
        mongo.db.feed.insert_one({"user_id": user.get('_id'), "post": feed_post})
        return {
            "message": "created post"
        }


@app.route('/feed')
@login_required
def post_feed():
    current_user_id = get_current_user().get('_id')
    pipeline = [
        {
            "$match": {"fake": True}
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
    feed = json_util.dumps(list(mongo.db.posts.aggregate(pipeline)))
    return feed


