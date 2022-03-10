from typing import Literal, Optional, Union, cast
from .github_client import github_call
from .commits import CommitRange
import json
import logging
import httpx

log = logging.getLogger(__name__)

CommitStatus = Union[Literal['failure'], Literal['error'], Literal['success'], Literal['pending']]


class GithubReporter(object):
    def __init__(self, commit_range: CommitRange, statuses_url: str) -> None:
        self.cr = commit_range
        self.statuses_url = statuses_url

    def _req(
        self, service: str, state: CommitStatus, description: Optional[Union[str, BaseException]]
    ) -> httpx.Response:
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

    def fail(self, service: str, message: Union[str, BaseException]) -> bool:
        resp = self._req(service, 'failure', message)
        return resp.status_code == httpx.codes.OK

    def error(self, service: str, message: Union[str, BaseException]) -> bool:
        resp = self._req(service, 'error', message)
        return resp.status_code == httpx.codes.OK

    def ok(self, service: str) -> bool:
        resp = self._req(service, 'success', None)
        return resp.status_code == httpx.codes.OK

    def pending(self, service: str) -> bool:
        resp = self._req(service, 'pending', None)
        return resp.status_code == httpx.codes.OK
