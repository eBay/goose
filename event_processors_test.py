import urllib.request
import json

import event_processors as ep

ALARM_CONFIG = ep.ConfigEntry('https://example.org/webhook', exact=['alarms.yml'])
NO_EXACT_CONFIG = ep.ConfigEntry('https://example.org/webhook')
NONMATCH_CONFIG = ep.ConfigEntry('https://example.org/webhook', exact=['zoomie'])


def test_process_push__exactmatch(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        def urlopen_mock(url, *args, **kwargs):
            assert url == 'https://example.org/webhook'
        monkeypatch.setattr(ep, 'get_file_contents_at_sha', lambda x,y: {})
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        ep.Processor([{'alarms': ALARM_CONFIG}]).process_push(data)

def test_process_push__nocommit(monkeypatch):
    with open('./test/push.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        def urlopen_mock(url, *args, **kwargs):
            assert False, "Shouldn't have called the service"
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        ep.Processor([{'alarms': ALARM_CONFIG}]).process_push(data)

def test_process_push__nomatch(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        def urlopen_mock(url, *args, **kwargs):
            assert False, "Shouldn't have called the service"
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        ep.Processor([{'alarms': NONMATCH_CONFIG}]).process_push(data)

def test_process_push__noexact(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        def urlopen_mock(url, *args, **kwargs):
            assert False, "Shouldn't have called the service"
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        ep.Processor([{'alarms': NO_EXACT_CONFIG}]).process_push(data)

def test_process_push__sends_content(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        def urlopen_mock(url, *args, **kwargs):
            assert 'data' in kwargs
            assert kwargs['data']['files']['alarms.yml'] == "alarm content"
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)
        monkeypatch.setattr(ep, 'get_file_contents_at_sha', lambda x,y: {
            'alarms.yml': "alarm content"
        })

        ep.Processor([{'alarms': ALARM_CONFIG}]).process_push(data)
