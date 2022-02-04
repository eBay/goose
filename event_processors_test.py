import urllib.request
from http.client import HTTPResponse
import json

from unittest.mock import MagicMock, Mock
import event_processors as ep
import pytest

ALARM_CONFIG = ep.ConfigEntry('alarms', 'https://example.org/webhook', exact=['alarms.yml'])
NO_EXACT_CONFIG = ep.ConfigEntry('noexact', 'https://example.org/webhook')
NONMATCH_CONFIG = ep.ConfigEntry('nonmatch', 'https://example.org/webhook', exact=['zoomie'])

fake_successful_http_response = Mock(spec=HTTPResponse)
fake_successful_http_response.headers = {}
fake_successful_http_response.status = 200

fake_error_response = Mock(spect=HTTPResponse)
fake_error_response.status = 500
fake_error_response.readlines.return_value = [b'it', b'works']




def test_process_push__exactmatch(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        mm = MagicMock()
        mm().repo_url = 'https://example.org'
        mm().files_changed.return_value = {'alarms.yml'}
        mm().get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}
        monkeypatch.setattr(ep, 'CommitRange', mm)


        def urlopen_mock(req, *args, **kwargs):
            assert req.full_url == 'https://example.org/webhook'
            assert 'application/json' in req.headers.get('Content-type', {})
            return fake_successful_http_response

        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        ep.Processor([{'alarms': ALARM_CONFIG}]).process_push(data)

def test_process_push__nomatch(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))


        mm = MagicMock()
        mm().files_changed.return_value = {'unknown'}
        monkeypatch.setattr(ep, 'CommitRange', mm)


        def urlopen_mock(url, *args, **kwargs):
            assert False, "Shouldn't have called the service"
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        ep.Processor([{'alarms': NONMATCH_CONFIG}]).process_push(data)

def test_process_push__noexact(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        mm = MagicMock()
        mm().files_changed.return_value = {'unknown'}
        monkeypatch.setattr(ep, 'CommitRange', mm)

        def urlopen_mock(url, *args, **kwargs):
            assert False, "Shouldn't have called the service"
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        ep.Processor([{'alarms': NO_EXACT_CONFIG}]).process_push(data)

def test_process_push__sends_content(monkeypatch):
    with open('./test/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        mm = MagicMock()
        # Why isn't this required?
        #     mm().repo_url = 'https://example.org'

        mm().files_changed.return_value = {'alarms.yml'}
        monkeypatch.setattr(ep, 'CommitRange', mm)

        def urlopen_mock(url, *args, **kwargs):
            assert 'data' in kwargs
            assert kwargs['data']['eventTimestamp'] == '2022-01-13T15:56:21-08:00'
            source = kwargs['data']['source']
            assert source['uri'] == 'https://github.corp.ebay.com/jabrahms/henrybot'
            assert kwargs['data']['type'] == 'COMMIT'
            item = kwargs['data']['files'][0]
            assert item['filepath'] == 'alarms.yml'
            assert item['matchType'] == 'EXACT_MATCH'
            assert item['contents']['new'] == "alarm content"
            assert 'old' not in item['contents']
        monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

        ep.Processor([{'alarms': ALARM_CONFIG}]).process_push(data)

def test_pr__excludes_irrelevant_events():
    with open('./test/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    data['action'] = 'assigned'
    retval = ep.Processor([{'alarms': ALARM_CONFIG}]).process_pull_request(data)
    assert retval == False, "Shouldn't have a match since the action isn't correct"

def test_pr__sends_update_for_known_file(monkeypatch):
    with open('./test/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    def urlopen_mock(url, *args, **kwargs):
        assert True, "Should have called the service"
        return fake_successful_http_response
    monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

    mm = MagicMock()
    mm().repo_url = 'https://example.org'
    mm().files_changed.return_value = {'alarms.yml'}
    mm().get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}
    monkeypatch.setattr(ep, 'CommitRange', mm)

    retval = ep.Processor([{'alarms': ALARM_CONFIG}]).process_pull_request(data)
    assert retval == True, "Should match"


def test_raw_update_function(monkeypatch):
    def urlopen_mock(url, *args, **kwargs):
        assert True, "Should have called the service"
        return fake_successful_http_response
    monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

    with open('./test/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    rng = MagicMock();
    rng.repo_url = 'https://example.org'
    rng.files_changed.return_value = {'alarms.yml'}
    rng.get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}

    retval = ep.Processor([{'alarms': ALARM_CONFIG}])._send_update(rng, outboundType='VERIFY', eventTimestamp='')
    assert retval == True


def test_raw_update__error(monkeypatch):
    def urlopen_mock(url, *args, **kwargs):
        assert True, "Should have called the service"
        return fake_error_response
    monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

    with open('./test/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    rng = MagicMock();
    rng.repo_url = 'https://example.org'
    rng.files_changed.return_value = {'alarms.yml'}
    rng.get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}

    retval = ep.Processor([{'alarms': ALARM_CONFIG}])._send_update(rng, outboundType='VERIFY', eventTimestamp='')
    assert retval == True


def test_raw_update__multiple_configs(monkeypatch):
    def urlopen_mock(url, *args, **kwargs):
        assert True, "Should have called the service"
        return fake_successful_http_response
    monkeypatch.setattr(urllib.request, 'urlopen', urlopen_mock)

    with open('./test/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    rng = MagicMock();
    rng.repo_url = 'https://example.org'
    rng.files_changed.return_value = {'alarms.yml'}
    rng.get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}

    processor = ep.Processor([
        {'_noop': NONMATCH_CONFIG},
        {'zzalarms': ALARM_CONFIG},
        {'tst': NO_EXACT_CONFIG},
    ])

    retval = processor._send_update(rng, outboundType='VERIFY', eventTimestamp='')
    assert retval == True
