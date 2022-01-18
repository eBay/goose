from urllib import request
from collections import namedtuple
from git import Git, Repo
import fs
import tempfile

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

        latest_commit = CommitInfo(event['repository']['git_url'], event['head_commit']['id'])

        relevant = set()
        for commit in event.get('commits', []):
            relevant |= set(
                commit['added'] +
                commit['removed'] +
                commit['modified']
            )

        for url, exact_set in self.url_to_exact.items():
            exact_matches = relevant.intersection(exact_set)
            if len(exact_matches) == 0:
                return

            files = get_file_contents_at_sha(exact_matches, latest_commit)
            request.urlopen(url, data={"files": files})
