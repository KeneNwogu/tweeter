from bson import ObjectId


def post_likes_aggregation_pipeline(post_id):
    post_pipeline = [
        {
            "$match": {"post": ObjectId(post_id)}
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
            "password_hash": 0,
            "bookmarks": 0,
            "following": 0,
            "followers": 0
        }}
    ]
    return post_pipeline
