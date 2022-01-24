import datetime
import os
import secrets

import jwt
from flask import request, make_response
from flask_cors import cross_origin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from tweeter import app, ALLOWED_EXTENSIONS
from tweeter.api.auth import login_required, get_current_user
from tweeter.api.errors import bad_request
from tweeter import mongo
from tweeter.utitlities import valid_email, gravatar_profile_image


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        data = request.get_json(force=True)
        if 'email' not in data:
            return bad_request("Invalid request format")

        if mongo.db.users.find_one({"email": data['email']}):
            return bad_request('please use a different email address')

        if not valid_email(data['email']):
            return bad_request('An invalid email was provided')

        password_hash = generate_password_hash(data['password'])
        # TODO gravitar profile image
        email = data['email']
        profile_image = gravatar_profile_image(email)
        user_data = {
            "email": email,
            "username": email,
            "password_hash": password_hash,
            "profile_image": profile_image,
            "bio": "Hey there! I'm using Tweeter"
        }
        user = mongo.db.users.insert_one(user_data)
        return {"message": "successfully registered user"}


@app.route('/login', methods=['POST'])
@cross_origin()
def login():
    if request.method == 'POST':
        data = request.get_json(force=True)
        if 'email' not in data or 'password' not in data:
            return bad_request("Email or username not provided")
        email = data['email']
        password = data['password']
        user = mongo.db.users.find_one({"email": email})
        if user:
            if check_password_hash(user.get('password_hash'), password):
                # perform login
                payload = {
                    "user_id": str(user.get('_id')),
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=35),
                    'iat': datetime.datetime.utcnow()
                }
                # set jwt
                token = jwt.encode(payload, app.config['SECRET_KEY'], "HS256")
                data = {
                    "message": "successfully logged in user",
                    "token": token,
                    "username": user.get('username'),
                    "bio": user.get('bio'),
                    "profile_image": user.get('profile_image')
                }
                response = make_response(data, 201)
                return response
        return bad_request("Invalid email or password")


@app.route('/users')
@login_required
def view_users():
    user = get_current_user()
    print(user)
    return {"message": "you are allowed"}


@app.route('/posts/create', methods=['POST'])
@login_required
def create_post():
    user = get_current_user()
    form = request.form
    caption = form.get('caption')
    file = request.files.get('file')

    # a file or caption must be provided
    if not (caption or file) or (caption == '' and file.filename == ''):
        return bad_request("must provide a caption or image")

    else:
        if file.filename != '':
            # handle file upload and posting
            filename = secure_filename(file.filename)
            _, ext = os.path.splitext(filename)
            revised_filename = _ + secrets.token_hex(6) + ext
            filename = revised_filename
            if ext not in ALLOWED_EXTENSIONS:
                return bad_request("file extension not allowed")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            post = mongo.db.posts.insert_one({"caption": caption, "post_url": filename, "user": user})
            # TODO create socket and broadcast to user's followers
            return {"message": file.filename}
        else:
            mongo.db.posts.insert_one({"caption": caption, "user": user})

    return {"message": "fix it"}

