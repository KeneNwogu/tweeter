import os

import jwt
import datetime
import pytest

from tweeter import app, mongo

logged_in_user = mongo.db.users.find_one({
    "email": 'test_email@test.com',
})


@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client
        mongo.db.posts.drop()
        mongo.db.followers.drop()
        mongo.db.comments.drop()
        mongo.db.likes.drop()


@pytest.fixture(scope='module')
def headers():
    # create test user
    payload = {
        "user_id": str(logged_in_user.get('_id')),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
        'iat': datetime.datetime.utcnow()
    }
    # set jwt
    secret = os.environ.get('SECRET_KEY') or 'you-dey-waste-your-time'
    token = jwt.encode(payload, secret, "HS256")
    return {
        'Authorization': token,
        'user_id': str(logged_in_user.get('_id')) # to get user id for testing, not required in actual headers
    }


@pytest.fixture(scope='module')
def mock_post():
    user = mongo.db.users.find_one({
        "email": 'test_email@test.com',
    })

    post = mongo.db.posts.insert_one({"caption": 'test caption', "post_urls": [], "user": user.get('_id'),
                                      "restricted": False, 'comments': 0, 'retweets': 0, 'likes': 0,
                                      'createdAt': datetime.datetime.utcnow()
                                      })

    return str(post.inserted_id)


@pytest.fixture(scope='module')
def mock_user():
    user = mongo.db.users.find_one({
        "email": 'test_email@test.com',
    })
    return str(user.get('_id'))