from bson import ObjectId, json_util
from tweeter import mongo


def test_profile(client, headers):
    user_id = headers.get('user_id')
    url = f'/{user_id}/profile'
    response = client.get(url, headers=headers)
    data = json_util.loads(response.data)
    assert response.status_code == 200
    assert data.get('self') is True
    assert data.get('follows_you') is False


def test_bookmarks(client, headers, mock_post):
    url = f'/{mock_post}/bookmark'
    response = client.get(url, headers=headers)
    data = json_util.loads(response.data)
    assert response.status_code == 200
    assert data['message'] == 'success'


def test_user_bookmarks(client, headers, mock_post):
    url = f'/{mock_post}/bookmark'
    response = client.get(url, headers=headers)

    url = f'/bookmarks'
    response = client.get(url, headers=headers)
    data = json_util.loads(response.data)
    assert response.status_code == 200
    assert type(data) == dict
    assert type(data['bookmarks']) == list


def test_user_retweet(client, headers, mock_post):
    url = f'/{mock_post}/retweet'
    response = client.get(url, headers=headers)
    assert response.status_code == 200


def test_user_posts(client, headers):
    user_id = headers.get('user_id')
    url = f'/user/{user_id}/posts'
    response = client.get(url, headers=headers)
    assert response.status_code == 200


def test_user_likes(client, headers):
    user_id = headers.get('user_id')
    url = f'/user/{user_id}/likes'
    response = client.get(url, headers=headers)
    assert response.status_code == 200


def test_user_media(client, headers):
    user_id = headers.get('user_id')
    url = f'/user/{user_id}/media'
    response = client.get(url, headers=headers)
    assert response.status_code == 200


def test_user_suggestions(client):
    url = f'/users/suggestions'
    response = client.get(url)
    assert response.status_code == 200