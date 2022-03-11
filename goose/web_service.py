from typing import Any, List, Optional, Callable
import json
import logging
from logging.config import fileConfig
import os
from pathlib import Path
import sys
import yaml
from quart import Quart, request
from quart.wrappers import Response
from .event_processors import Processor, ConfigEntry

REPO_ROOT = Path(__file__).resolve().parent.parent
fileConfig(f'{REPO_ROOT}/logging.cfg')


log = logging.getLogger(__name__)


def uncaught_exception_handler(exctype: Any, value: Any, traceback: Any) -> Any:
    log.exception('Uncaught exception', extra={'exctype': exctype, 'value': value, 'tb': traceback})  # pragma: no cover


sys.excepthook = uncaught_exception_handler


COMMIT_INFO = None
if os.path.exists(f'{REPO_ROOT}/git-info.txt'):
    with open(f'{REPO_ROOT}/git-info.txt', encoding='utf-8') as commit_file:  # pragma: no cover
        COMMIT_INFO = ''.join(commit_file.readlines())


def get_processor_list() -> List[ConfigEntry]:
    processor_list = []
    config_file = os.environ.get('GOOSE_CONFIG', '/etc/goose.yaml')
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        for entry in cfg:
            processor_list.append(ConfigEntry.from_yaml_entry(entry))
    return processor_list


process = Processor(get_processor_list())

GITHUB_EVENT_NAME_HEADER = 'X-GitHub-Event'
FOUND_WEBHOOK_HEADER = 'did-process'
MATCHED_HEADER = 'did-match-rule'

app = Quart(__name__)


@app.route('/')
async def index() -> str:
    log.info("Index")
    return f"works: {COMMIT_INFO}"


@app.route('/webhook', methods=['POST'])
async def webhook() -> Response:
    log.info("webhook")
    # TODO: Emit metric on payload size. Github caps events at 25mb.
    event = request.headers.get(GITHUB_EVENT_NAME_HEADER)
    # TODO: hmac validation of incoming payload
    log.info("Incoming event: %s", event)

    j = await (request.get_json())
    log.debug("incoming JSON payload", extra={"json": json.dumps(j, indent=2)})

    # Dispatch to a method called e.g. process_foo when the event type is "foo".
    p: Optional[Callable[[Any], bool]] = getattr(process, f'process_{event}', None)
    log.debug('Has method for the %s event? %s', event, p is not None)
    processed = 'no'
    matched_rule = 'no'
    if p is not None:
        if p((await request.get_json())):
            matched_rule = 'yes'
        processed = 'yes'
    else:
        log.debug("Unable to find a handler for event: %s", event)
    return Response({}, 200, {FOUND_WEBHOOK_HEADER: processed, MATCHED_HEADER: matched_rule})


if __name__ == '__main__':
    app.run()
