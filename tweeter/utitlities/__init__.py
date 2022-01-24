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
    base_url = 'https://www.gravatar.com/avatar?'
    default = {'d': 'monsterid'}
    email_hash = hashlib.md5(email.encode()).hexdigest()
    req = requests.models.PreparedRequest()
    url = urljoin(base_url, email_hash)
    req.prepare_url(url, params=default)
    return req.url


print(gravatar_profile_image('test@test.com'))


