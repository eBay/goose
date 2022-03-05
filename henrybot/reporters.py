from typing import Literal, Optional, Union
from urllib import request, parse
from .github_client import github_call
import json

CommitStatus = Union[Literal['failure'], Literal['error'], Literal['success'], Literal['pending']]

class GithubReporter(object):
    def __init__(self, commit_range, statuses_url):
        self.cr = commit_range
        self.statuses_url = statuses_url

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

        return github_call(self.statuses_url.replace('{sha}', sha), body)

    def fail(self, service: str, message: str):
        self._req(service, 'failure', message)

    def error(self, service: str, message: str):
        self._req(service, 'error', message)

    def ok(self, service: str):
        self._req(service, 'success', None)

    def pending(self, service: str):
        self._req(service, 'pending', None)
