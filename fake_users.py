import csv
from tweeter.utitlities import gravatar_profile_image
from pymongo import MongoClient

# mongodb connections
client = MongoClient('')
db = client.tweeter_test
users = db['users']
posts = db['posts']

# csv file handling
file = open('tweeter/utitlities/resolutions_tweet_data.csv', 'r', encoding='utf-8', errors='replace')
reader = csv.reader(file)
headers = next(reader)
print(headers)

fake_email = "test_tweeter@gmail.com"
for i in range(15):
    tweet = next(reader)
    user_data = {
        "email": fake_email,
        "username": tweet[3],
        "bio": "Hey there! I'm using tweeter.",
        "profile_image": gravatar_profile_image(fake_email),
        "fake": True
    }
    # insert user here
    user = users.insert_one(user_data).inserted_id

    caption = tweet[6]
    tweet_data = {
        "caption": caption,
        "post_urls": [],
        "user": user,
        "restricted": False,
        "fake": True
    }
    post = posts.insert_one(tweet_data)

