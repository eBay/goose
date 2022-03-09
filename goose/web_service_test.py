from quart import Quart
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import asyncio
from . import web_service as ws
CWD = Path(__file__).resolve().parent


@pytest.mark.asyncio
async def test_index():
    test_client = ws.app.test_client()
    response = await test_client.get('/')
    assert b'works' in (await response.get_data())

@pytest.mark.asyncio
async def test_unknown_webhook():
    test_client = ws.app.test_client()

    with open(f'{CWD}/fixtures/push_with_commits.event.json') as f:
        data = ''.join(f.readlines())

    response = await test_client.post('/webhook', json=data, headers={
        ws.GITHUB_EVENT_NAME_HEADER: 'unknown',
    })

    assert ws.FOUND_WEBHOOK_HEADER in response.headers, "Couldn't find {} in the headers".format(ws.FOUND_WEBHOOK_HEADER)
    assert response.headers[ws.FOUND_WEBHOOK_HEADER] == 'no'

@pytest.mark.asyncio
async def test_known_webhook(monkeypatch):
    test_client = ws.app.test_client()


    with open(f'{CWD}/fixtures/push_with_commits.event.json') as f:
        data = ''.join(f.readlines())

    def the_test(info):
        assert info == data

    monkeypatch.setattr(ws.process, 'process_push', the_test)

    response = await test_client.post('/webhook', json=data, headers={
        ws.GITHUB_EVENT_NAME_HEADER: 'push',
    })

    assert ws.FOUND_WEBHOOK_HEADER in response.headers, "Couldn't find {} in the headers".format(ws.FOUND_WEBHOOK_HEADER)
    assert response.headers[ws.FOUND_WEBHOOK_HEADER] == 'yes'

def test_config_loading(monkeypatch):
    mock_open = MagicMock()
    mock_open().__enter__.return_value = '''
- name: name-here
  owner: person@example.org
  url: https://example.org
  filePatterns:
    - testing
    '''

    mock_os = MagicMock()
    mock_os.path.exists.return_value = True
    monkeypatch.setattr(ws, 'os', mock_os)

    with patch('goose.web_service.open', mock_open, create=True):
        result = ws.get_processor_list()
    assert len(result) == 1
    assert result[0].name == 'name-here'
    assert result[0].url == 'https://example.org'
    assert result[0].exact == ['testing']
