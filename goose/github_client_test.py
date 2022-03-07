import json
from unittest.mock import MagicMock
from . import github_client as gc

def test_auth_repo_url(monkeypatch):
    monkeypatch.setattr(gc, 'GITHUB_USERNAME', 'test')
    monkeypatch.setattr(gc, 'GITHUB_PASSWORD', 'value')
    retval = gc.create_authenticated_repo_url('http://google.com')
    assert retval == 'http://test:value@google.com'


def test_default_branch_name(monkeypatch):
    req = MagicMock()
    # Eew. No file-like object though b/c StringIO can't handle bytes.
    req.urlopen.return_value.readlines.return_value = [bytes(json.dumps({'default_branch': 'main'}), 'utf-8')]
    monkeypatch.setattr(gc, 'request', req)
    assert gc.get_default_branch_name('owner', 'repo') == 'main'
