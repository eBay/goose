from urllib import request, parse, error
from collections import namedtuple
import os
import fs
import tempfile
import json
import logging
import re
from datetime import datetime
from .reporters import GithubReporter
from .commits import CommitRange, prune_dotgit_suffix, sha_doesnt_exist
from .github_client import get_default_branch_name, get_pull_request

log = logging.getLogger(__name__)

ROOT_SERVICE_NAME = 'goose'
retest_matcher = re.compile(r'retest (?P<root>'+ ROOT_SERVICE_NAME + r')(/(?P<subservice>\w+))?')


class ConfigEntry(object):
    def __init__(self, name, url, exact=None):
        self.name = name
        self.url = url
        self.exact = exact or []

    def return_matches(self, files):
        'Given a filename, does it match this config?'
        return set(self.exact).intersection(files)




class Processor(object):
    def __init__(self, config):
        self.config = config;

    def _build_payload(self, matches, commitRange, eventTimestamp, outboundType, repo_url):
        files = commitRange.get_file_contents_at_latest(matches)

        if type(eventTimestamp) == int:
            eventTimestamp = datetime.fromtimestamp(eventTimestamp).isoformat()

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

    def _call_service(self, url, data):
        log.info(f"Calling {url} with data: {data}")
        req = request.Request(
            url,
            data=bytes(json.dumps(data), encoding='utf-8'),
            headers={
                'content-type': 'application/json'
            },
            method='POST',
        )
        response = request.urlopen(req)
        log.debug(f"response headers: {response.headers}")
        return response

    def _send_update(self, commitRange, outboundType, eventTimestamp, status_url, only_run=None):
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
                # TODO: Refactor this http exception handling away when we move to requests
                try:
                    response = self._call_service(matcher.url, payload)
                    reporter.ok(service)
                except error.HTTPError as e:
                    if e.code >= 400 and e.code < 500:
                        reporter.fail(service, e.reason)
                    else:
                        reporter.error(service, e.reason)

        reporter.ok(ROOT_SERVICE_NAME)
        return found_match

    def process_push(self, event):
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

    def process_pull_request(self, event):
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

    def process_issue_comment(self, event):
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
            pr_info['repository']['clone_url'],
            pr_info['pull_request']['base']['sha'],
            pr_info['pull_request']['head']['sha'],
        )

        return self._send_update(
            commitRange,
            outboundType='VERIFY',
            eventTimestamp=pr_info['pull_request']['updated_at'],
            status_url=pr_info['repository']['statuses_url'],
            **kwargs
        )
