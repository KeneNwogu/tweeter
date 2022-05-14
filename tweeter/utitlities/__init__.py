import datetime
import os
import re
import hashlib
from urllib.parse import urlencode, urlparse
from urllib.request import urljoin

import bson
import jwt
import requests
from bson import ObjectId
from cloudinary.uploader import upload
from werkzeug.utils import secure_filename

from tweeter import app, ALLOWED_EXTENSIONS
from tweeter.api.errors import bad_request


def create_register_jwt(user_id, secret):
    payload = {
        "user_id": str(user_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=50),
        'iat': datetime.datetime.utcnow()
    }
    # set jwt
    token = jwt.encode(payload, secret, "HS256")
    return token


def valid_email(email):
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if re.search(regex, email):
        return True
    return False


def gravatar_profile_image(email: str):
    default = {'d': 'retro'}
    email_hash = hashlib.md5(email.encode())
    email_hash = email_hash.hexdigest()
    base_url = f'https://www.gravatar.com/avatar/{email_hash}?'
    req = requests.models.PreparedRequest()
    req.prepare_url(base_url, params=default)
    return req.url


def cloudinary_file_upload(file):
    data = upload(file)
    return data.get('url')


def upload_files(files):
    post_urls = []
    for file in files:
        if file.filename != '':
            # handle file upload and posting
            filename = secure_filename(file.filename)
            _, ext = os.path.splitext(filename)
            if ext not in ALLOWED_EXTENSIONS:
                return bad_request("file extension not allowed")

            url = cloudinary_file_upload(file)
            post_urls.append(url)
    return post_urls


def validate_id(_id):
    try:
        _id = ObjectId(_id)
    except (bson.errors.InvalidId, TypeError):
        return bad_request(f"Invalid userID of {_id} was passed in the url")
    else:
        return _id
