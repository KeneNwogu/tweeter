import datetime

from bson import json_util, ObjectId
from tweeter import mongo


def test_likes(client, mock_post, headers):
    """

    :param client:
    :param mock_post:
    :param headers:
    :return:

    GIVEN: given a mock post
    WHEN: the /post/like endpoint is hit
    THEN: A success message should be received and the updated post should have an increase in likes
    """
    post = mongo.db.posts.find_one({'_id': ObjectId(mock_post)})
    old_likes = post['likes']

    url = f'/{mock_post}/like'
    response = client.get(url, headers=headers)
    data = json_util.loads(response.data)

    updated_post = mongo.db.posts.find_one({'_id': ObjectId(mock_post)})
    new_likes = updated_post['likes']
    assert response.status_code == 200
    assert data['message'] == 'success'
    assert data['liked'] is True
    assert new_likes > old_likes


def test_double_liking_unlikes_post(client, mock_user, headers):
    """
    :param client:
    :param mock_user:
    :param headers:
    :return:

    GIVEN: given a mock post
    WHEN: the /post/like endpoint is hit twice for the same user
    THEN: A success message should be received and the updated post should have a decrease in likes
    """
    mock_post = mongo.db.posts.insert_one({
        "caption": 'test caption', "post_urls": [], "user": mock_user,
        "restricted": False, 'comments': 0, 'retweets': 0, 'likes': 0,
        'createdAt': datetime.datetime.utcnow()
    }).inserted_id

    post = mongo.db.posts.find_one({'_id': ObjectId(mock_post)})
    old_likes = post['likes']

    url = f'/{mock_post}/like'
    response = client.get(url, headers=headers)
    data = json_util.loads(response.data)
    updated_post = mongo.db.posts.find_one({'_id': ObjectId(mock_post)})
    new_likes = updated_post['likes']

    assert response.status_code == 200
    assert data['message'] == 'success'
    assert data['liked'] is True
    assert new_likes - old_likes == 1

    post = mongo.db.posts.find_one({'_id': ObjectId(mock_post)})
    old_likes = post['likes']

    second_response = client.get(url, headers=headers)
    data = json_util.loads(second_response.data)
    updated_post = mongo.db.posts.find_one({'_id': ObjectId(mock_post)})
    new_likes = updated_post['likes']

    assert response.status_code == 200
    assert data['message'] == 'success'
    assert data['liked'] is False
    assert new_likes < old_likes
