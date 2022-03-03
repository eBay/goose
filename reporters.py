from typing import Literal, Optional, Union
from urllib import request, parse
import json

CommitStatus = Union[Literal['failed'], Literal['error'], Literal['success'], Literal['pending']]

class GithubReporter(object):
    def __init__(self, commit_range):
        self.cr = commit_range

    def _req(self, service, state: CommitStatus, description: Optional[str]):
        owner, repo = self.cr.owner_repo
        sha = self.cr.head_sha
        body = {
            'owner': owner,
            'repo': repo,
            'sha': sha,
            'state': state,
            'context': f'henrybot/{service}',
        }

        if description:
            body['description'] = description

        # @@@ Give this the proper base url.
        url = f'https://example.org/repos/{owner}/{repo}/statuses/{sha}'
        req = request.Request(
            url,
            data=bytes(json.dumps(body), encoding='utf-8'),
            headers={
                'content-type': 'application/json'
            },
            method='POST',
        )

        response = request.urlopen(req)
        return response

    def fail(self, service: str, message: str):
        self._req(service, 'failed', message)

    def error(self, service: str, message: str):
        self._req(service, 'error', message)

    def ok(self, service: str):
        self._req(service, 'success', None)

    def pending(self, service: str):
        self._req(service, 'pending', None)
