from typing import Dict, Any, Union
from urllib import parse
import base64
import os
import logging
import httpx

log = logging.getLogger(__name__)
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
GITHUB_PASSWORD = os.environ.get('GITHUB_PASSWORD')
GithubPullRequestEvent = Dict[Any, Any]

if None in (GITHUB_USERNAME, GITHUB_PASSWORD):  # pragma: no cover
    try:
        # These are placed there by the kubernetes system
        with open('/etc/secrets/GITHUB_USERNAME', 'r', encoding='utf-8') as f:
            GITHUB_USERNAME = f.read()
        with open('/etc/secrets/GITHUB_PASSWORD', 'r', encoding='utf-8') as f:
            GITHUB_PASSWORD = f.read()
    except FileNotFoundError:
        pass


def create_authenticated_repo_url(url: str) -> str:
    if GITHUB_PASSWORD is None or GITHUB_USERNAME is None:
        log.warning("Not authenticating request. Unknown github credentials")
        return url
    parsed = parse.urlparse(url)
    updated = parsed._replace(netloc=f"{GITHUB_USERNAME}:{GITHUB_PASSWORD}@{parsed.netloc}")
    return parse.urlunparse(updated)


def _auth_header() -> Dict[str, str]:
    token = (base64.b64encode(bytes(f'{GITHUB_USERNAME}:{GITHUB_PASSWORD}', 'utf-8')).decode('utf-8'),)
    return {'authorization': f'Basic {token}'}


def github_call(url: str, body: Any) -> httpx.Response:
    log.debug("github request: %s to %s", body, url)
    return httpx.post(url, headers=_auth_header(), json=body)


def _get_json(url: str) -> Any:
    return httpx.get(url, headers=_auth_header()).json()


def get_default_branch_name(url: str) -> str:
    data: Dict[str, Union[str, Any]] = _get_json(url)
    return data['default_branch']


def get_pull_request(pr_url: str) -> GithubPullRequestEvent:
    data: GithubPullRequestEvent = _get_json(pr_url)
    return data
