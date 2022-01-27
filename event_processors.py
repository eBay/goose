from urllib import request
from collections import namedtuple
from git import Git, Repo
import fs
import tempfile
import logging

log = logging.getLogger(__name__)

class ConfigEntry(object):
    def __init__(self, url, exact=None):
        self.url = url
        self.exact = exact or []

CommitInfo = namedtuple('CommitInfo', ['repo_url', 'sha'])

def get_file_contents_at_sha(files, commit_info):
    output = {}
    # map of filename to file contents
    with tempfile.TemporaryDirectory() as tmpdirname:
        # TODO: shallower clone, ideally.
        repo = Repo.clone_from(commit_info.repo_url, tmpdirname)
        commit = repo.commit(commit_info.sha)
        for f in files:
            blob = commit.tree.join(f)
            # TODO: NPE?
            data = ''.join([x.decode('utf-8') for x in blob.data_stream.stream.readlines()])
            output[f] = data

    return output

class Processor(object):
    def __init__(self, config):
        self.config = config;
        self.url_to_exact = {}
        for obj in config:
            for name, cfg in obj.items():
                self.url_to_exact[cfg.url] = set(cfg.exact)


    def process_push(self, event):
        log.info("Processing a push")
        latest_commit = CommitInfo(event['repository']['git_url'], event['head_commit']['id'])

        relevant = set()
        commits = event.get('commits', [])
        for commit in commits:
            relevant |= set(
                commit['added'] +
                commit['removed'] +
                commit['modified']
            )

        files_payload = []
        for url, exact_set in self.url_to_exact.items():
            exact_matches = relevant.intersection(exact_set)
            if len(exact_matches) == 0:
                log.info("Unable to find exact matches in the payload")
                return
            log.info(f"Seems we've found an exact match with files: {exact_matches}")

            files = get_file_contents_at_sha(exact_matches, latest_commit)

            log.info(f"file-contents: {files}. Sending it to {url}")
            files_payload += [{'filepath': x,
                               'matchType': 'EXACT_MATCH',
                               'contents': {'new': y},
                               } for x,y in files.items()]
        data={
            "files": files_payload,
            "eventTimestamp": commits[0]['timestamp'],
            "type": "COMMIT",
            "source": {
                "uri": event['repository']['url']
            }
        }
        request.urlopen(url, data=data)
