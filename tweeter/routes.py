import datetime

import jwt
from bson import json_util, ObjectId
from flask import request, make_response
from flask_cors import cross_origin
from werkzeug.security import check_password_hash

from tweeter import app
from tweeter import mongo
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import bad_request
from tweeter.utitlities import upload_files


@app.route('/health', methods=['GET'])
def health_check():
    return "Healthy"


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
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=720),
                    'iat': datetime.datetime.utcnow()
                }
                # set jwt
                token = jwt.encode(payload, app.config['SECRET_KEY'], "HS256")
                data = {
                    "message": "successfully logged in user",
                    "token": token,
                    "_id": str(user.get('_id')),
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
    # if not (caption or files) or (caption == '' and files == []):
    #     return bad_request("must provide a caption or image")

    if not caption and not files:
        return bad_request("must provide a caption or image")

    else:
        post_urls = upload_files(files)
        post = mongo.db.posts.insert_one({"caption": caption, "post_urls": post_urls, "user": user.get('_id'),
                                          "restricted": restricted, 'comments': 0, 'retweets': 0, 'likes': 0,
                                          'saves': 0, 'createdAt': datetime.datetime.utcnow()
                                          })
        # TODO create socket and broadcast to user's followers
        data = {
            "message": "created post",
            "post_id": str(post.inserted_id),
            "user": user
        }
        return json_util.dumps(data)


@app.route('/feed')
@login_required
def post_feed():
    current_user_id = get_current_user().get('_id')
    user_bookmarks = mongo.db.users.find_one({'_id': current_user_id}).get('bookmarks', [])
    # following = list(mongo.db.followers.find({'follower': current_user_id}))
    # following_ids = list(map(lambda x: x.get('user'), following))

    user_likes = list(mongo.db.likes.find({'user': current_user_id, 'post': {"$ne": None}}))
    liked_posts = list(map(lambda x: x.get('post'), user_likes))
    pipeline = [
        # {
        #     "$match": {
        #         "$or": [{"fake": True}, {"user": {"$in": following_ids}}, {"user": current_user_id}]
        #     },
        # },
        {
            "$lookup": {
                "from": "users",
                "localField": "user",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},
        {"$project": {
            "caption": 1,
            "post_urls": 1,
            "user": 1,
            "restricted": 1,
            'comments': 1,
            'retweets': 1,
            'likes': 1,
            'saves': 1,
            'retweeted_by': 1,
            'createdAt': 1
        }},
        {"$sort": {"createdAt": -1}}
    ]
    response = list(mongo.db.posts.aggregate(pipeline))
    for post in response:
        retweeted_by = post.get('retweeted_by', [])  # user ids

        post['liked'] = True if post.get('_id') in liked_posts else False
        post['saved'] = True if post.get('_id') in user_bookmarks else False
        post['retweeted'] = True if current_user_id in retweeted_by else False

    feed = json_util.dumps(response)
    return feed


@app.route('/search/<keyword>')
@login_required
def search(keyword):
    pipeline = [
        {
            "$match": {
                "caption": {"$regex": keyword, "$options": "i"}
            },
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"},
        {"$project": {
            "user.password_hash": 0,
            "user.bookmarks": 0,
            "user.following": 0,
            "user.followers": 0,
            "user.bio": 0
        }},
        {"$sort": {"createdAt": -1}}
    ]
    posts = list(mongo.db.posts.aggregate(pipeline))
    current_user_id = get_current_user().get('_id')
    user_bookmarks = mongo.db.users.find_one({'_id': current_user_id}).get('bookmarks', [])
    user_likes = list(mongo.db.likes.find({'user': current_user_id, 'post': {"$ne": None}}))
    liked_posts = list(map(lambda x: x.get('post'), user_likes))

    for post in posts:
        retweeted_by = post.get('retweeted_by', [])  # user ids

        post['liked'] = True if post.get('_id') in liked_posts else False
        post['saved'] = True if post.get('_id') in user_bookmarks else False
        post['retweeted'] = True if current_user_id in retweeted_by else False

    users = list(mongo.db.users.find({"username": {"$regex": keyword, "$options": "i"}}))
    for user in users:
        if str(current_user_id) == str(user.get('_id')):
            user['self'] = True
            user['follows_you'] = False
            user['you_follow'] = False
        else:
            user['self'] = False
            user['you_follow'] = True if mongo.db.followers.find_one({
                'user': ObjectId(user.get('_id')),
                'follower': ObjectId(current_user_id)
            }) else False
            user['follows_you'] = True if mongo.db.followers.find_one({
                'user': ObjectId(current_user_id),
                'follower': ObjectId(user.get('_id'))
            }) else False
    response_data = {
        'posts': posts,
        'users': users
    }
    return json_util.dumps(response_data)


@app.route('/users/suggestions')
def user_suggestions():
    recent_users = list(mongo.db.users.find({'fake': {"$ne": True}},
                                            {'password_hash': 0, 'bookmarks': 0}).limit(5).sort('createdAt', -1))
    current_user = get_current_user()
    if current_user:
        current_user_id = current_user.get('_id')
        for user in recent_users:
            if str(current_user_id) == str(user.get('_id')):
                user['self'] = True
                user['follows_you'] = False
                user['you_follow'] = False
            else:
                user['self'] = False
                user['you_follow'] = True if mongo.db.followers.find_one({
                    'user': ObjectId(user.get('_id')),
                    'follower': ObjectId(current_user_id)
                }) else False
                user['follows_you'] = True if mongo.db.followers.find_one({
                    'user': ObjectId(current_user_id),
                    'follower': ObjectId(user.get('_id'))
                }) else False
    return json_util.dumps(recent_users)