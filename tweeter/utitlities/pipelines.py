from bson import ObjectId


def post_aggregation_pipeline(post_id):
    post_pipeline = [
        {
            "$match": {"_id": ObjectId(post_id)}
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": "$user"}
    ]
    return post_pipeline
