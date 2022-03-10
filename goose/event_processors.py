from typing import List, Optional, Set, Dict, Union, Literal, Iterable, cast, Any, TypedDict
import os
import fs
import tempfile
import json
import logging
import re
import pytz
import httpx
from datetime import datetime
from .reporters import GithubReporter
from .commits import CommitRange, prune_dotgit_suffix, sha_doesnt_exist
from .github_client import get_default_branch_name, get_pull_request, GithubPullRequestEvent

log = logging.getLogger(__name__)

ROOT_SERVICE_NAME = 'goose'
retest_matcher = re.compile(r'retest (?P<root>' + ROOT_SERVICE_NAME + r')(/(?P<subservice>\w+))?')

GithubPushEvent = Dict[Any, Any]
GithubIssueCommentEvent = Dict[Any, Any]


class ConfigEntry(object):
    def __init__(self, name: str, url: str, exact: Optional[List[str]] = None) -> None:
        self.name = name
        self.url = url
        self.exact = set(exact or [])

    def return_matches(self, files: Iterable[str]) -> Set[str]:
        'Given a filename, does it match this config?'
        return self.exact.intersection(files)


OutboundType = Union[Literal['VERIFY'], Literal['COMMIT']]

class GitSource(TypedDict):
    uri: str
    sha: str

class FileInfo(TypedDict):
    filepath: str
    matchType: Literal['EXACT_MATCH']
    contents: Dict[str, str]

class OutboundPayload(TypedDict):
    app_id: str
    files: List[FileInfo]
    eventTimestamp: str
    type: OutboundType
    source: GitSource




class Processor(object):
    def __init__(self, config: Iterable[ConfigEntry]) -> None:
        self.config = config;

    def _build_payload(self, matches: Iterable[str], commitRange: CommitRange,
                       eventTimestamp: str, outboundType: OutboundType, repo_url: str) -> OutboundPayload:
        files = commitRange.get_file_contents_at_latest(matches)

        if isinstance(eventTimestamp, int):
            eventTimestamp = datetime.fromtimestamp(eventTimestamp, pytz.timezone("UTC")).isoformat()

        return {
            "app_id": "_".join(commitRange.owner_repo),
            "files": [{'filepath': x,
                       'matchType': 'EXACT_MATCH',
                       'contents': {'new': y},
                       } for x, y in files.items()],
            "eventTimestamp": eventTimestamp,
            "type": outboundType,
            "source": {
                "uri": prune_dotgit_suffix(repo_url),
                "sha": commitRange.head_sha,
            }
        }

    def _call_service(self, url: str, data: Any) -> httpx.Response:
        log.info(f"Calling {url} with data: {data}")
        return httpx.post(url, json=data)

    def _send_update(self, commitRange: CommitRange, outboundType: OutboundType,
                     eventTimestamp: str, status_url: str, only_run: Optional[List[str]]=None) -> bool:
        '''
        Conceptually, a request comes in. We look through our config, and find
        out if there are any relevant matches. If there are, we send out
        requests to upstream systems to get their info. We also report out to
        github with status.
        '''
        relevant = commitRange.files_changed()

        reporter = GithubReporter(commitRange, status_url)
        reporter.pending(ROOT_SERVICE_NAME)
        found_match = False
        for matcher in self.config:
            service = matcher.name
            if only_run is not None and service not in only_run:
                continue
            matches = matcher.return_matches(relevant)
            if matches:
                found_match = True
                reporter.pending(service)
                payload = self._build_payload(matches, commitRange, eventTimestamp, outboundType, commitRange.repo_url)
                response = self._call_service(matcher.url, payload)
                if response.status_code < 400:
                    reporter.ok(service)
                elif response.status_code >= 400 and response.status_code < 500:
                    reporter.fail(service, response.text)
                else:
                    reporter.error(service, response.text)

        reporter.ok(ROOT_SERVICE_NAME)
        return found_match

    def process_push(self, event: GithubPushEvent) -> bool:
        """
        https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#push
        """
        log.info("Processing a push")

        if sha_doesnt_exist(event['after']):
            # Push to delete a branch
            return False

        # If this push isn't to the default branch, we don't operate on it.
        if event['ref'][len('refs/heads/'):] != get_default_branch_name(*event['repository']['full_name'].split('/')):
            return False

        commitRange = CommitRange(
            event['repository']['clone_url'],
            event['before'],
            event['after']
        )

        return self._send_update(
            commitRange,
            outboundType='COMMIT',
            # NB: Pushed at, not updated at. https://stackoverflow.com/a/15922637/4972
            eventTimestamp=event['repository']['pushed_at'],
            status_url=event['repository']['statuses_url'],
        )

    def process_pull_request(self, event: GithubPullRequestEvent) -> bool:
        """
        https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#pull_request
        """
        if event['action'] not in ("opened", "reopened", "synchronize"):
            return False

        commitRange = CommitRange(
            event['repository']['clone_url'],
            event['pull_request']['base']['sha'],
            event['pull_request']['head']['sha'],
        )

        return self._send_update(
            commitRange,
            outboundType='VERIFY',
            eventTimestamp=event['pull_request']['updated_at'],
            status_url=event['repository']['statuses_url'],
        )

    def process_issue_comment(self, event: GithubIssueCommentEvent) -> bool:
        pr = event['issue']['pull_request']['url']
        comment = event['comment']['body'].lower()
        match = retest_matcher.match(comment)
        if match is None:
            return False
        limited_to = match.groupdict().get('subservice')
        kwargs = {}
        if limited_to:
            kwargs = {'only_run': [limited_to]}

        pr_info = get_pull_request(pr)
        commitRange = CommitRange(
            pr_info['head']['repo']['clone_url'],
            pr_info['base']['sha'],
            pr_info['head']['sha'],
        )

        return self._send_update(
            commitRange,
            outboundType='VERIFY',
            eventTimestamp=pr_info['updated_at'],
            status_url=pr_info['head']['repo']['statuses_url'],
            **kwargs
        )
