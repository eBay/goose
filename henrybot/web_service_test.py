from quart import Quart
from pathlib import Path
import pytest
import asyncio
from .web_service import GITHUB_EVENT_NAME_HEADER, FOUND_WEBHOOK_HEADER, app, process
CWD = Path(__file__).resolve().parent


@pytest.mark.asyncio
async def test_index():
    test_client = app.test_client()
    response = await test_client.get('/')
    assert b'works' in (await response.get_data())

@pytest.mark.asyncio
async def test_unknown_webhook():
    test_client = app.test_client()

    with open(f'{CWD}/test/push_with_commits.event.json') as f:
        data = ''.join(f.readlines())

    response = await test_client.post('/webhook', json=data, headers={
        GITHUB_EVENT_NAME_HEADER: 'unknown',
    })

    assert FOUND_WEBHOOK_HEADER in response.headers, "Couldn't find {} in the headers".format(FOUND_WEBHOOK_HEADER)
    assert response.headers[FOUND_WEBHOOK_HEADER] == 'no'

@pytest.mark.asyncio
async def test_known_webhook(monkeypatch):
    test_client = app.test_client()


    with open(f'{CWD}/test/push_with_commits.event.json') as f:
        data = ''.join(f.readlines())

    def the_test(info):
        assert info == data

    monkeypatch.setattr(process, 'process_push', the_test)

    response = await test_client.post('/webhook', json=data, headers={
        GITHUB_EVENT_NAME_HEADER: 'push',
    })

    assert FOUND_WEBHOOK_HEADER in response.headers, "Couldn't find {} in the headers".format(FOUND_WEBHOOK_HEADER)
    assert response.headers[FOUND_WEBHOOK_HEADER] == 'yes'
