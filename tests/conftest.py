import os

import jwt
import datetime
import pytest

from tweeter import app, mongo

logged_in_user = mongo.db.users.insert_one({
    "email": 'test_email@test.com',
    "username": 'Test User Header',
    "password_hash": 'hashed password',
    "profile_image": 'fake_profile_image_url',
    "bio": "Hey there! I'm using Tweeter",
    "followers": 0,
    "following": 0
})


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(scope='module')
def headers():
    # create test user
    payload = {
        "user_id": str(logged_in_user.inserted_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
        'iat': datetime.datetime.utcnow()
    }
    # set jwt
    secret = os.environ.get('SECRET_KEY') or 'you-dey-waste-your-time'
    token = jwt.encode(payload, secret, "HS256")
    return {
        'Authorization': token
    }


@pytest.fixture(scope='module')
def mock_post():
    user = mongo.db.users.insert_one({
        "email": 'test_email@test.com',
        "username": 'Test User',
        "password_hash": 'hashed password',
        "profile_image": 'fake_profile_image_url',
        "bio": "Hey there! I'm using Tweeter",
        "followers": 0,
        "following": 0
    })

    post = mongo.db.posts.insert_one({"caption": 'test caption', "post_urls": [], "user": user.inserted_id,
                                      "restricted": False, 'comments': 0, 'retweets': 0, 'likes': 0,
                                      'createdAt': datetime.datetime.utcnow()
                                      })
    # comments = mongo.db.comments.insert_one({
    #     'post': post.inserted_id,
    #     'caption': 'This is a test comment',
    #     'images': [],
    #     'comments': 0,
    #     'retweets': 0,
    #     'likes': 0,
    #     'user': user,
    #     'createdAt': datetime.datetime.utcnow()
    # })
    return str(post.inserted_id)


@pytest.fixture(scope='module')
def mock_user():
    user = mongo.db.users.insert_one({
        "email": 'test_email@test.com',
        "username": 'Test User',
        "password_hash": 'hashed password',
        "profile_image": 'fake_profile_image_url',
        "bio": "Hey there! I'm using Tweeter",
        "followers": 0,
        "following": 0
    })
    return str(user.inserted_id)