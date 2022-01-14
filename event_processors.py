from urllib import request

class ConfigEntry(object):
    def __init__(self, url, exact=None):
        self.url = url
        self.exact = exact or []


class Processor(object):
    def __init__(self, config):
        self.config = config;

    def process_push(self, event):
        for commit in event.get('commits', []):
            relevant = set(
                commit['added'] +
                commit['removed'] +
                commit['modified']
            )

            for entry in self.config:
                for name, config in entry.items():
                    exact_matches = relevant.intersection(set(config.exact))
                    if len(exact_matches) != 0:
                         request.urlopen(config.url)
