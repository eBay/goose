from . import github_client as gc

def test_auth_repo_url(monkeypatch):
    monkeypatch.setattr(gc, 'GITHUB_USERNAME', 'test')
    monkeypatch.setattr(gc, 'GITHUB_PASSWORD', 'value')
    retval = gc.create_authenticated_repo_url('http://google.com')
    assert retval == 'http://test:value@google.com'
