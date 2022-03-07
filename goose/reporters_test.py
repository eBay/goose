from unittest.mock import MagicMock
from urllib import request, response
from .event_processors import CommitRange
from .reporters import GithubReporter
import json

status_url = 'https://github.corp.ebay.com/api/v3/repos/jabrahms/henrybot/statuses/{sha}'

def test_reporter__service_call(monkeypatch):
    cr = CommitRange('https://github.com/ebay/test-repo', 'start', 'end')
    reporter = GithubReporter(cr, status_url)

    def urlopen_mock(req, *args, **kwargs):
        data = json.loads(req.data)
        assert data['owner'] == 'ebay'
        assert data['repo'] == 'test-repo'
        assert data['sha'] == 'end'
        assert data['context'] == 'goose/servicename'
        assert data['state'] == 'success'
        assert 'description' not in data

    monkeypatch.setattr(request, 'urlopen', urlopen_mock)

    reporter.ok('servicename')

def test_reporter__service_call_pending(monkeypatch):
    cr = CommitRange('https://github.com/ebay/test-repo', 'start', 'end')
    reporter = GithubReporter(cr, status_url)

    def urlopen_mock(req, *args, **kwargs):
        data = json.loads(req.data)
        assert data['state'] == 'pending'
        assert 'description' not in data

    monkeypatch.setattr(request, 'urlopen', urlopen_mock)

    reporter.pending('servicename')


def test_reporter__service_call_fail(monkeypatch):
    cr = CommitRange('https://github.com/ebay/test-repo', 'start', 'end')
    reporter = GithubReporter(cr, status_url)

    def urlopen_mock(req, *args, **kwargs):
        data = json.loads(req.data)
        assert data['state'] == 'failure'
        assert data['description'] == 'message here'

    monkeypatch.setattr(request, 'urlopen', urlopen_mock)

    reporter.fail('servicename', 'message here')

def test_reporter__service_call_error(monkeypatch):
    cr = CommitRange('https://github.com/ebay/test-repo', 'start', 'end')
    reporter = GithubReporter(cr, status_url)

    def urlopen_mock(req, *args, **kwargs):
        data = json.loads(req.data)
        assert data['state'] == 'error'
        assert data['description'] == 'message here'

    monkeypatch.setattr(request, 'urlopen', urlopen_mock)

    reporter.error('servicename', 'message here')
