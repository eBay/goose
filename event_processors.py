from urllib import request
from collections import namedtuple
from git import Git, Repo
import fs
import tempfile
import logging
import json

log = logging.getLogger(__name__)

class ConfigEntry(object):
    def __init__(self, name, url, exact=None):
        self.name = name
        self.url = url
        self.exact = exact or []


class CommitRange(object):
    def __init__(self, repo_url, start, end):
        self.repo_url = repo_url
        self.start = start
        self.end = end
        self.repo = None
        self.tmpdir = None

    def _get_git_repo(self):
        if self.repo is None:
            # setup clone stuff.
            self.tmpdir = tempfile.TemporaryDirectory()

            # TODO: shallower clone, ideally.
            self.repo = Repo.clone_from(self.repo_url, self.tmpdir.name)
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
        self.url_to_exact = {}
        for obj in config:
            for name, cfg in obj.items():
                self.url_to_exact[cfg.name] = (cfg.url, set(cfg.exact))

    def _send_update(self, commitRange, outboundType, eventTimestamp):
        relevant = commitRange.files_changed()

        files_payload = []
        for url, exact_set in self.url_to_exact.values():
            exact_matches = relevant.intersection(exact_set)
            if len(exact_matches) == 0:
                log.info("Unable to find exact matches in the payload")
                continue

            log.info(f"Seems we've found an exact match with files: {exact_matches}")

            files = commitRange.get_file_contents_at_latest(exact_matches)

            log.info(f"file-contents: {files}. Sending it to {url}")
            files_payload += [{'filepath': x,
                               'matchType': 'EXACT_MATCH',
                               'contents': {'new': y},
                               } for x, y in files.items()]

        if len(files_payload) == 0:
            return False

        data={
            "files": files_payload,
            "eventTimestamp": eventTimestamp,
            "type": outboundType,
            "source": {
                "uri": commitRange.repo_url,
            }
        }

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
        if response.status >= 400:
            txt = ''.join([x.decode('utf-8') for x in response.readlines()])
            log.warn(f"Failure on http call: {txt}")
        return True

    def process_push(self, event):
        """
        https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#push
        """

        log.info("Processing a push")

        commitRange = CommitRange(event['repository']['git_url'],
                                  event['before'],
                                  event['after'])

        return self._send_update(
            commitRange,
            outboundType='COMMIT',
            eventTimestamp=event['repository']['updated_at'],
        )

    def process_pull_request(self, event):
        """
        https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#pull_request
        """
        if event['action'] not in ("opened", "reopened", "synchronize"):
            return False

        commitRange = CommitRange(
            event['repository']['git_url'],
            event['pull_request']['base']['sha'],
            event['pull_request']['head']['sha'],
        )

        return self._send_update(
            commitRange,
            outboundType='VERIFY',
            eventTimestamp=event['pull_request']['updated_at'],
        )
