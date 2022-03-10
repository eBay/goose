from pathlib import Path
import json
import os
import httpx

from unittest.mock import MagicMock, Mock
from . import event_processors as ep
from .reporters import GithubReporter
import pytest

ALARM_CONFIG = ep.ConfigEntry('alarms', 'https://example.org/webhook', exact=['alarms.yml'])
NO_EXACT_CONFIG = ep.ConfigEntry('noexact', 'https://example.org/webhook')
NONMATCH_CONFIG = ep.ConfigEntry('nonmatch', 'https://example.org/webhook', exact=['zoomie'])

fake_successful_http_response = Mock(spec=httpx.Response)
fake_successful_http_response.status_code = 200
fake_successful_http_response.text = ''

CWD = Path(__file__).resolve().parent


def test_commit_range__parse_url_to_owner():
    cr = ep.CommitRange('https://github.com/ebay/thing', 'sha1', 'sha2')
    assert cr.owner_repo == ('ebay', 'thing')

def test_commit_range__parse_git_url():
    cr = ep.CommitRange('https://github.com/ebay/thing.git', 'sha1', 'sha2')
    assert cr.owner_repo == ('ebay', 'thing')

def test_commit_range__head_sha():
    cr = ep.CommitRange('https://github.com/ebay/thing.git', 'sha1', 'sha2')
    assert cr.head_sha == 'sha2'

def test_process_push__non_default_branch_push(monkeypatch):
    with open(f'{CWD}/fixtures/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    bn = MagicMock()
    bn.return_value = 'unmatched'
    monkeypatch.setattr(ep, 'get_default_branch_name', bn)

    assert ep.Processor([ALARM_CONFIG]).process_push(data) == False

def test_process_push__exactmatch(monkeypatch):
    with open(f'{CWD}/fixtures/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        mm = MagicMock()
        mm().repo_url = 'https://example.org'
        mm().files_changed.return_value = {'alarms.yml'}
        mm().get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}
        mm().owner_repo = ('owner', 'repo')
        mm().head_sha = 'sha'
        monkeypatch.setattr(ep, 'CommitRange', mm)

        monkeypatch.setattr(ep, 'GithubReporter', MagicMock())
        bn = MagicMock()
        bn.return_value = 'foo'
        monkeypatch.setattr(ep, 'get_default_branch_name', bn)

        httpx_mock = MagicMock()
        httpx_mock.post.return_value = fake_successful_http_response
        monkeypatch.setattr(ep, 'httpx', httpx_mock)


        assert ep.Processor([ALARM_CONFIG]).process_push(data)

        assert httpx_mock.post.call_count == 1
        args = httpx_mock.post.call_args[0]
        assert args[0] == 'https://example.org/webhook'

def test_process_push__delete(monkeypatch):
    with open(f'{CWD}/fixtures/branch-delete.push.json') as f:
        data = json.loads(''.join(f.readlines()))
    assert ep.Processor([NONMATCH_CONFIG]).process_push(data) == False

def test_process_push__nomatch(monkeypatch):
    with open(f'{CWD}/fixtures/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        mm = MagicMock()
        mm().files_changed.return_value = {'unknown'}
        mm().owner_repo = ('owner', 'repo')
        mm().head_sha = 'sha'
        monkeypatch.setattr(ep, 'CommitRange', mm)
        monkeypatch.setattr(ep, 'GithubReporter', MagicMock())

        bn = MagicMock()
        bn.return_value = 'foo'
        monkeypatch.setattr(ep, 'get_default_branch_name', bn)

        httpx_mock = MagicMock()
        monkeypatch.setattr(ep, 'httpx', httpx_mock)

        assert ep.Processor([NONMATCH_CONFIG]).process_push(data) == False
        assert not httpx_mock.post.called

def test_process_push__noexact(monkeypatch):
    with open(f'{CWD}/fixtures/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        mm = MagicMock()
        mm().files_changed.return_value = {'unknown'}
        mm().owner_repo = ('owner', 'repo')
        mm().head_sha = 'sha'
        monkeypatch.setattr(ep, 'CommitRange', mm)
        monkeypatch.setattr(ep, 'GithubReporter', MagicMock())

        bn = MagicMock()
        bn.return_value = 'foo'
        monkeypatch.setattr(ep, 'get_default_branch_name', bn)

        httpx_mock = MagicMock()
        monkeypatch.setattr(ep, 'httpx', httpx_mock)

        assert ep.Processor([NO_EXACT_CONFIG]).process_push(data) == False
        assert not httpx_mock.post.called

def test_process_push__sends_content(monkeypatch):
    with open(f'{CWD}/fixtures/push_with_commits.event.json') as f:
        data = json.loads(''.join(f.readlines()))

        mm = MagicMock()
        mm().repo_url = 'https://example.org'
        mm().files_changed.return_value = {'alarms.yml'}
        mm().owner_repo = ('owner', 'repo')
        mm().head_sha = 'sha'
        mm().get_file_contents_at_latest.return_value = {'alarms.yml': 'alarm content'}
        monkeypatch.setattr(ep, 'CommitRange', mm)
        monkeypatch.setattr(ep, 'GithubReporter', MagicMock())

        bn = MagicMock()
        bn.return_value = 'foo'
        monkeypatch.setattr(ep, 'get_default_branch_name', bn)


        httpx_mock = MagicMock()
        httpx_mock.post.return_value = fake_successful_http_response
        monkeypatch.setattr(ep, 'httpx', httpx_mock)

        assert ep.Processor([ALARM_CONFIG]).process_push(data)
        args, kwargs = httpx_mock.post.call_args
        assert args[0] == 'https://example.org/webhook'

        assert kwargs == {
            'json': {
                'app_id': 'owner_repo',
                'eventTimestamp': '2022-01-13T23:56:27+00:00',
                'source': {
                    'uri': 'https://example.org',
                    'sha': 'sha'
                },
                'type': 'COMMIT',
                'files': [{
                    'filepath': 'alarms.yml',
                    'matchType': 'EXACT_MATCH',
                    'contents': {
                        'new': 'alarm content'
                    }
                }]
            }
        }

def test_pr__excludes_irrelevant_events():
    with open(f'{CWD}/fixtures/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    data['action'] = 'assigned'
    retval = ep.Processor([ALARM_CONFIG]).process_pull_request(data)
    assert retval == False, "Shouldn't have a match since the action isn't correct"

def test_pr__sends_update_for_known_file(monkeypatch):
    with open(f'{CWD}/fixtures/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    httpx_mock = MagicMock()
    httpx_mock.post.return_value = fake_successful_http_response
    monkeypatch.setattr(ep, 'httpx', httpx_mock)

    mm = MagicMock()
    mm().repo_url = 'https://example.org'
    mm().head_sha = 'sha'
    mm().owner_repo = ('owner', 'repo')
    mm().files_changed.return_value = {'alarms.yml'}
    mm().get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}
    monkeypatch.setattr(ep, 'CommitRange', mm)
    monkeypatch.setattr(ep, 'GithubReporter', MagicMock())

    assert ep.Processor([ALARM_CONFIG]).process_pull_request(data)


def test_raw_update_function(monkeypatch):
    httpx_mock = MagicMock()
    httpx_mock.post.return_value = fake_successful_http_response
    monkeypatch.setattr(ep, 'httpx', httpx_mock)
    monkeypatch.setattr(ep, 'GithubReporter', MagicMock())

    with open(f'{CWD}/fixtures/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    rng = MagicMock();
    rng.repo_url = 'https://example.org'
    rng.owner_repo = ('owner', 'repo')
    rng.head_sha = 'sha'
    rng.files_changed.return_value = {'alarms.yml'}
    rng.get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}

    retval = ep.Processor([ALARM_CONFIG])._send_update(rng, outboundType='VERIFY', eventTimestamp='', status_url='')
    assert retval == True

def test_raw_update_function__skip_unspecified(monkeypatch):
    monkeypatch.setattr(ep, 'GithubReporter', MagicMock())

    with open(f'{CWD}/fixtures/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    commitRange = MagicMock();

    retval = ep.Processor([ALARM_CONFIG])._send_update(
        commitRange, outboundType='VERIFY', eventTimestamp='', status_url='',
        only_run=['foo'])
    assert retval == False


def test_raw_update__error(monkeypatch):
    httpx_mock = MagicMock()
    error = Mock(spec=httpx.Response)
    error.status_code = 400
    httpx_mock.post.return_value = error
    monkeypatch.setattr(ep, 'httpx', httpx_mock)
    monkeypatch.setattr(ep, 'GithubReporter', MagicMock())

    with open(f'{CWD}/fixtures/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    rng = MagicMock();
    rng.repo_url = 'https://example.org'
    rng.head_sha = 'sha'
    rng.owner_repo = ('owner', 'repo')
    rng.files_changed.return_value = {'alarms.yml'}
    rng.get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}

    retval = ep.Processor([ALARM_CONFIG])._send_update(rng, outboundType='VERIFY', eventTimestamp='', status_url='')
    assert retval == True


def test_raw_update__multiple_configs(monkeypatch):
    def httpx_mock(request, *args, **kwargs):
        assert True, "Should have called the service"
        return fake_successful_http_response
    httpx_mock = MagicMock()
    httpx_mock.post.return_value = fake_successful_http_response
    monkeypatch.setattr(ep, 'httpx', httpx_mock)
    monkeypatch.setattr(ep, 'GithubReporter', MagicMock())

    with open(f'{CWD}/fixtures/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    rng = MagicMock();
    rng.repo_url = 'https://example.org'
    rng.owner_repo = ('owner', 'repo')
    rng.head_sha = 'sha'
    rng.files_changed.return_value = {'alarms.yml'}
    rng.get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}

    processor = ep.Processor([
        NONMATCH_CONFIG,
        ALARM_CONFIG,
        NO_EXACT_CONFIG,
    ])

    retval = processor._send_update(rng, outboundType='VERIFY', eventTimestamp='', status_url='')
    assert retval == True

@pytest.mark.parametrize("code,reporter_method_called", [
    (200, 'ok'),
    (400,'fail'),
    (500,'error'),
])
def test_update__reports_error(code, reporter_method_called, monkeypatch):
    def call_mock(request, *args, **kwargs):
        resp = Mock(spec=httpx.Response)
        resp.status_code = code
        resp.text = 'it works'
        return resp

    monkeypatch.setattr(httpx, 'post', call_mock)
    reporter = MagicMock()
    monkeypatch.setattr(ep, 'GithubReporter', reporter)

    with open(f'{CWD}/fixtures/pr.event.json') as f:
        data = json.loads(''.join(f.readlines()))

    rng = MagicMock();
    rng.repo_url = 'https://example.org'
    rng.head_sha = 'sha'
    rng.owner_repo = ('owner', 'repo')
    rng.files_changed.return_value = {'alarms.yml'}
    rng.get_file_contents_at_latest.return_value = {'alarms.yml': 'file contents'}

    processor = ep.Processor([
        NONMATCH_CONFIG,
        ALARM_CONFIG,
        NO_EXACT_CONFIG,
    ])

    processor._send_update(rng, outboundType='VERIFY', eventTimestamp='', status_url='')

    assert reporter().pending.called
    assert getattr(reporter(), reporter_method_called).called

def test_retest__bare():
    assert ep.retest_matcher.match('retest') is None

def test_retest__goose():
    m = ep.retest_matcher.match('retest goose')
    assert m is not None
    assert m['subservice'] is None

def test_retest__subservice():
    m = ep.retest_matcher.match('retest goose/foo')
    assert m is not None
    assert m['subservice'] == 'foo'

def test_retest__no_slash():
    m = ep.retest_matcher.match('retest goosefoo')
    assert m is not None
    assert m['subservice'] is None


def test_pr_comment__not_retest():
    event = {
        'issue': {'pull_request': {'url': 'https://example.org'}},
        'comment': {'body': '🎉'},
    }
    processor = ep.Processor([
        NONMATCH_CONFIG,
        ALARM_CONFIG,
        NO_EXACT_CONFIG,
    ])
    assert processor.process_issue_comment(event) == False

def test_pr_comment__retest_single(monkeypatch):
    event = {
        'issue': {'pull_request': {'url': 'https://example.org'}},
        'comment': {'body': 'retest goose/alarms'},
    }

    gpr = MagicMock()
    monkeypatch.setattr(ep, 'get_pull_request', gpr)

    processor = ep.Processor([
        ALARM_CONFIG,
    ])

    processor._send_update = MagicMock()
    processor.process_issue_comment(event)

    assert processor._send_update.called

def test_pr_comment__retest_all(monkeypatch):
    event = {
        'issue': {'pull_request': {'url': 'https://example.org'}},
        'comment': {'body': 'retest goose'},
    }
    gpr = MagicMock()
    monkeypatch.setattr(ep, 'get_pull_request', gpr)
    processor = ep.Processor([
        NONMATCH_CONFIG,
        ALARM_CONFIG,
        NO_EXACT_CONFIG,
    ])
    processor._send_update = MagicMock()
    processor.process_issue_comment(event)

    assert processor._send_update.called
    assert 'only_run' not in processor._send_update.call_args or \
        processor._send_update.call_args.kwargs['only_run'] is None
