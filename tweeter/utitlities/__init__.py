import re
import hashlib
from urllib.parse import urlencode, urlparse
from urllib.request import urljoin
import requests


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


# print(gravatar_profile_image("GeeksforGeeks"))


