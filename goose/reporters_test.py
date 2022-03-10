from collections import namedtuple
from unittest.mock import MagicMock
from .event_processors import CommitRange
from . import reporters
import json

status_url = 'https://github.corp.ebay.com/api/v3/repos/jabrahms/henrybot/statuses/{sha}'

response = namedtuple('Response', ['status_code'])
success_response = response(200)


def test_reporter__service_call(monkeypatch):
    cr = CommitRange('https://github.com/ebay/test-repo', 'start', 'end')
    reporter = reporters.GithubReporter(cr, status_url)

    def call_mock(url, data):
        assert data['owner'] == 'ebay'
        assert data['repo'] == 'test-repo'
        assert data['sha'] == 'end'
        assert data['context'] == 'goose/servicename'
        assert data['state'] == 'success'
        assert 'description' not in data
        return success_response

    monkeypatch.setattr(reporters, 'github_call', call_mock)

    assert reporter.ok('servicename') == True


def test_reporter__service_call_pending(monkeypatch):
    cr = CommitRange('https://github.com/ebay/test-repo', 'start', 'end')
    reporter = reporters.GithubReporter(cr, status_url)

    def call_mock(url, data):
        assert data['state'] == 'pending'
        assert 'description' not in data
        return success_response

    monkeypatch.setattr(reporters, 'github_call', call_mock)

    reporter.pending('servicename')


def test_reporter__service_call_fail(monkeypatch):
    cr = CommitRange('https://github.com/ebay/test-repo', 'start', 'end')
    reporter = reporters.GithubReporter(cr, status_url)

    def call_mock(url, data):
        assert data['state'] == 'failure'
        assert data['description'] == 'message here'
        return success_response

    monkeypatch.setattr(reporters, 'github_call', call_mock)

    reporter.fail('servicename', 'message here')


def test_reporter__service_call_error(monkeypatch):
    cr = CommitRange('https://github.com/ebay/test-repo', 'start', 'end')
    reporter = reporters.GithubReporter(cr, status_url)

    def call_mock(url, data):
        assert data['state'] == 'error'
        assert data['description'] == 'message here'
        return success_response

    monkeypatch.setattr(reporters, 'github_call', call_mock)

    assert reporter.error('servicename', 'message here')
