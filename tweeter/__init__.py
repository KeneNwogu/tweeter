import os

import cloudinary
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'you-dey-waste-your-time'
app.config['UPLOAD_FOLDER'] = 'tweeter/media'
app.config['MONGO_URI'] = os.environ.get('MONGO_URI') or 'mongodb://127.0.0.1:27017/tweeter_test'
app.config['CLOUDINARY_URL'] = os.environ.get('CLOUDINARY_URL')

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)


ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.mp4', '.mp3'}
mongo = PyMongo()
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")
mongo.init_app(app)

from tweeter import routes
from tweeter.comments.routes import comments
from tweeter.users.routes import users
from tweeter.posts.routes import posts

app.register_blueprint(comments)
app.register_blueprint(users)
app.register_blueprint(posts)
