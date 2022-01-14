import urllib.request
import json

from event_processors import ConfigEntry, Processor

ALARM_CONFIG = ConfigEntry('https://example.org/webhook', exact=['alarms.yml'])
NO_EXACT_CONFIG = ConfigEntry('https://example.org/webhook')
NONMATCH_CONFIG = ConfigEntry('https://example.org/webhook', exact=['zoomie'])



def test_process_push__exactmatch(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        def urlopen_mock(url, *args, **kwargs):
            assert url == 'https://example.org/webhook'
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)


        Processor([{'alarms': ALARM_CONFIG}]).process_push(data)

def test_process_push__nocommit(monkeypatch):
    with open('./test/push.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        def urlopen_mock(url, *args, **kwargs):
            assert False, "Shouldn't have called the service"
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        Processor([{'alarms': ALARM_CONFIG}]).process_push(data)

def test_process_push__nomatch(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        def urlopen_mock(url, *args, **kwargs):
            assert False, "Shouldn't have called the service"
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        Processor([{'alarms': NONMATCH_CONFIG}]).process_push(data)

def test_process_push__noexact(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        def urlopen_mock(url, *args, **kwargs):
            assert False, "Shouldn't have called the service"
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        Processor([{'alarms': NO_EXACT_CONFIG}]).process_push(data)
