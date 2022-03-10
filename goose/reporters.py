from typing import Literal, Optional, Union, cast
from http.client import HTTPResponse
from urllib import request, parse
from .github_client import github_call
from .commits import CommitRange
import json
import logging
log = logging.getLogger(__name__)

CommitStatus = Union[Literal['failure'], Literal['error'], Literal['success'], Literal['pending']]

class GithubReporter(object):
    def __init__(self, commit_range: CommitRange, statuses_url: str) -> None:
        self.cr = commit_range
        self.statuses_url = statuses_url

    def _req(self, service: str, state: CommitStatus, description: Optional[Union[str, BaseException]]) -> HTTPResponse:
        owner, repo = self.cr.owner_repo
        sha = self.cr.head_sha
        body = {
            'owner': owner,
            'repo': repo,
            'sha': sha,
            'state': state,
            'context': f'goose/{service}',
        }

        if description:
            body['description'] = cast(str, description)

        log.debug(f"Calling {owner}/{repo} with status {state} for service {service}")
        return github_call(self.statuses_url.replace('{sha}', sha), body)

    def fail(self, service: str, message: Union[str, BaseException]) -> None:
        self._req(service, 'failure', message)

    def error(self, service: str, message: Union[str, BaseException]) -> None:
        self._req(service, 'error', message)

    def ok(self, service: str) -> None:
        self._req(service, 'success', None)

    def pending(self, service: str) -> None:
        self._req(service, 'pending', None)
