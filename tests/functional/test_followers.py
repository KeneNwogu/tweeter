import datetime

from bson import json_util, ObjectId
from tweeter import mongo
from tests.conftest import logged_in_user

user1 = mongo.db.users.insert_one({
    "email": 'test_email@test.com',
    "username": 'Test User1',
    "password_hash": 'hashed password',
    "profile_image": 'fake_profile_image_url',
    "bio": "Hey there! I'm using Tweeter",
    "followers": 0,
    "following": 0
})

user2 = mongo.db.users.insert_one({
    "email": 'test_email@test.com',
    "username": 'Test User2',
    "password_hash": 'hashed password',
    "profile_image": 'fake_profile_image_url',
    "bio": "Hey there! I'm using Tweeter",
    "followers": 0,
    "following": 0
})


def test_followers_list(client, headers):
    _id = str(user1.inserted_id)
    url = f'/{_id}/followers'
    response = client.get(url, headers=headers)
    data = json_util.loads(response.data)

    assert response.status_code == 200
    assert type(data) == list


def test_following_list(client, headers):
    _id = str(user1.inserted_id)
    url = f'/{_id}/following'
    response = client.get(url, headers=headers)
    data = json_util.loads(response.data)

    assert response.status_code == 200
    assert type(data) == list


def test_follow_user(client, headers):
    follower = mongo.db.users.find_one({'_id': ObjectId(logged_in_user.inserted_id)})
    user = mongo.db.users.find_one({'_id': user2.inserted_id})
    old_followers = user.get('followers')
    url = f'/{str(user.get("_id"))}/follow'
    response = client.get(url, headers=headers)
    data = json_util.loads(response.data)

    assert response.status_code == 200
    followers = list(mongo.db.followers.find({'follower': follower.get('_id'), 'user': ObjectId(user.get('_id'))}))
    assert len(followers) > 0
    assert data['message'] == 'success'

    updated_user = mongo.db.users.find_one({'_id': user.get("_id")})
    new_followers = updated_user.get('followers')
    assert new_followers > old_followers
