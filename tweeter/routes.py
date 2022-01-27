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
from tweeter.utitlities import valid_email, gravatar_profile_image, cloudinary_file_upload, create_register_jwt


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
        token = create_register_jwt(user.inserted_id, app.config['SECRET_KEY'])
        return {
            "message": "successfully registered user",
            "token": token,
            "email": user_data.get('email'),
            "username": user_data.get('username'),
            "bio": user_data.get('bio'),
            "profile_image": user_data.get('profile_image')
        }


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
                    "email": user.get('email'),
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


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    if request.method == 'GET':
        data = {
            "username": user.get('username'),
            "email": user.get('email'),
            "bio": user.get('bio'),
            "followers": len(user.get('followers', [])),
            "following": len(user.get('following', [])),
            "profile_image": user.get('profile_image')
        }
        return data

    if request.method == 'POST':
        fields = ['username', 'bio']
        form = request.form
        profile_image = request.files.get('file')
        data = {}
        if not (data or profile_image) or (not data and profile_image.filename == ''):
            return bad_request('No data was provided')
        else:
            for field in fields:
                if form.get(field):
                    data[field] = form.get('field')
            if profile_image:
                if profile_image.filename != '':
                    new_profile_image = cloudinary_file_upload(profile_image)
                    data['profile_image'] = new_profile_image

            mongo.db.users.update_one({'_id': user.get('_id')}, {"$set": data})
            updated_user = mongo.db.users.find_one({'_id': user.get('_id')})
            return {
                "message": "successfully updated details",
                "username": updated_user.get('username'),
                "email": updated_user.get('email'),
                "bio": updated_user.get('bio'),
                "profile_image": updated_user.get('profile_image'),
            }
