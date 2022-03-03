from urllib import request, parse
from json_logs import get_logger
import base64
import os
import json

log = get_logger(__name__)
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
GITHUB_PASSWORD = os.environ.get('GITHUB_PASSWORD')

if None in (GITHUB_USERNAME, GITHUB_PASSWORD): # pragma: no cover
    try:
        # These are placed there by the kubernetes system
        GITHUB_USERNAME = open('/etc/secrets/GITHUB_USERNAME').read()
        GITHUB_PASSWORD = open('/etc/secrets/GITHUB_PASSWORD').read()
    except FileNotFoundError:
        pass


def create_authenticated_repo_url(url):
    if GITHUB_PASSWORD is None and GITHUB_USERNAME is None:
        log.warning("Not authenticating request. Unknown github credentials")
        return url
    parsed = parse.urlparse(url)
    assert parsed.username is None
    assert parsed.password is None
    updated = parsed._replace(netloc=f"{GITHUB_USERNAME}:{GITHUB_PASSWORD}@{parsed.netloc}")
    return parse.urlunparse(updated)


def github_call(url, body):
    req = request.Request(
        url,
        data=bytes(json.dumps(body), encoding='utf-8'),
        headers={
            'content-type': 'application/json',
            'authorization': 'Basic %s' % (base64.b64encode(bytes(f'{GITHUB_USERNAME}:{GITHUB_PASSWORD}', 'utf-8'))).decode('utf-8'),
        },
        method='POST',
    )

    response = request.urlopen(req)
    return response
