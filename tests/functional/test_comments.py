from bson import json_util, ObjectId
from tweeter import mongo


def test_comment_list(client, mock_post, headers):
    """

    :param client:
    :param mock_post:
    :param headers:
    :return:

    GIVEN: given a mock post
    WHEN: the /post/comments endpoint is hit [GET REQUEST]
    THEN: A status code of 200 and a list of comments should be received
    """
    url = f'/{mock_post}/comments'
    response = client.get(url, headers=headers)
    data = json_util.loads(response.data)
    assert response.status_code == 200
    assert type(data['comments']) == list


def test_comment_post(client, mock_post, headers):
    """

    :param client:
    :param mock_post:
    :param headers:
    :return:

    GIVEN: given a mock post
    WHEN: the /post/comments endpoint is hit [POST REQUEST]
    THEN: A status code of 200 and number of comments for the given post should be increased
    """
    post = mongo.db.posts.find_one({'_id': ObjectId(mock_post)})
    old_comments = post['comments']
    url = f'/{mock_post}/comments'
    data = {
        'caption': 'created test caption'
    }
    response = client.post(url, headers=headers, data=data)
    updated_post = mongo.db.posts.find_one({'_id': ObjectId(mock_post)})
    new_comments = updated_post['comments']
    assert response.status_code == 200
    assert new_comments > old_comments
    assert mongo.db.comments.find_one({'post': ObjectId(mock_post), 'caption': 'created test caption'}) is not None
