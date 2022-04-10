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
    assert type(data['bookmarks']) == dict
