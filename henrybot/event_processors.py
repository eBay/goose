from urllib import request, parse, error
from collections import namedtuple
from git import Git, Repo
import os
import fs
import tempfile
import json
import logging
from datetime import datetime
from .reporters import GithubReporter
from .github_client import create_authenticated_repo_url

log = logging.getLogger(__name__)

GONE_SHA = '0000000000000000000000000000000000000000'
ROOT_SERVICE_NAME='henrybot'


class ConfigEntry(object):
    def __init__(self, name, url, exact=None):
        self.name = name
        self.url = url
        self.exact = exact or []

    def return_matches(self, files):
        'Given a filename, does it match this config?'
        return set(self.exact).intersection(files)

def prune_dotgit_suffix(s):
    'if the string ends with .git, remove that'
    if s.endswith('.git'):
        return s[:-4]
    return s

class CommitRange(object):
    def __init__(self, repo_url, start, end):
        self.repo_url = repo_url
        # GitHub sends 0000 when the branch is new, for instance.
        if start == GONE_SHA:
            self.start = None
        else:
            self.start = start
        self.end = end
        self.repo = None
        self.tmpdir = None

    @property
    def owner_repo(self):
        parts = parse.urlparse(self.repo_url)
        (_, owner, repo, *rest) = parts.path.split('/')
        return (owner, prune_dotgit_suffix(repo))

    @property
    def head_sha(self):
        return self.end

    def _get_git_repo(self):
        if self.repo is None:
            # setup clone stuff.
            self.tmpdir = tempfile.TemporaryDirectory()

            # TODO: shallower clone, ideally.
            self.repo = Repo.clone_from(
                # Auth needs to happen here so we don't send repo url to
                # upstreams
                create_authenticated_repo_url(self.repo_url),
                self.tmpdir.name
            )
        return self.repo

    def files_changed(self):
        repo = self._get_git_repo()
        head_commit = repo.commit(self.end)
        base_commit = repo.commit(self.start)

        changed = set()
        diffs = head_commit.diff(base_commit)
        for diff in diffs:
            # in the case of a rename, we want to know if either side has
            # the file name we care about.
            changed |= {diff.a_path, diff.b_path}

        return changed

    def get_file_contents_at_latest(self, filenames):
        repo = self._get_git_repo()
        output = {}
        commit = repo.commit(self.end)
        for f in filenames:
            blob = commit.tree.join(f)
            # TODO: NPE?
            data = ''.join([x.decode('utf-8') for x in blob.data_stream.stream.readlines()])
            output[f] = data
        return output

    def __del__(self):
        del self.tmpdir  # not sure if this is necessary to clean up the temp file



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

    def _send_update(self, commitRange, outboundType, eventTimestamp, status_url):
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
                    elif e.code >= 500:
                        reporter.error(service, e.reason)

        reporter.ok(ROOT_SERVICE_NAME)
        return found_match

    def process_push(self, event):
        """
        https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#push
        """
        log.info("Processing a push")

        if event['after'] == GONE_SHA:
            # Push to delete a branch
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
