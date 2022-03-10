import json
from unittest.mock import MagicMock
from . import github_client as gc

def test_auth_repo_url(monkeypatch):
    monkeypatch.setattr(gc, 'GITHUB_USERNAME', 'test')
    monkeypatch.setattr(gc, 'GITHUB_PASSWORD', 'value')
    retval = gc.create_authenticated_repo_url('http://google.com')
    assert retval == 'http://test:value@google.com'

def test_auth_repo_url(monkeypatch):
    monkeypatch.setattr(gc, 'GITHUB_USERNAME', None)
    monkeypatch.setattr(gc, 'GITHUB_PASSWORD', None)
    retval = gc.create_authenticated_repo_url('http://google.com')
    assert retval == 'http://google.com'


def test_default_branch_name(monkeypatch):
    req = MagicMock()
    # Eew. No file-like object though b/c StringIO can't handle bytes.
    req.get.return_value.json.return_value = {'default_branch': 'main'}
    monkeypatch.setattr(gc, 'httpx', req)
    assert gc.get_default_branch_name('owner', 'repo') == 'main'

def test_pr_fetch(monkeypatch):
    m = MagicMock()
    m.return_value = 'the-json'
    monkeypatch.setattr(gc, '_get_json', m)
    resp = gc.get_pull_request('some url')
    assert resp == 'the-json'
    assert m.called_with('some-url')

def test_actually_makes_post(monkeypatch):
    m = MagicMock()
    monkeypatch.setattr(gc, 'httpx', m)

    resp = gc.github_call('some url', {'data': 1})
    assert m.post.called
