from bson import json_util

from tweeter import mongo


def test_feed_endpoint(client, headers):
    mongo.db.posts.insert_one({
        'caption': 'hello',
        'fake': True,
    })
    response = client.get('/feed', headers=headers)
    data = json_util.loads(response.data)
    assert response.status_code == 200
    assert type(data) == list
    # assert len(data) > 0


def test_search(client, headers):
    response = client.get('/search/test', headers=headers)
    assert response.status_code == 200
