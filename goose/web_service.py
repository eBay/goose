from typing import NoReturn, Any, List
import json
import os
import yaml
import sys
import logging
from pathlib import Path
from logging.config import fileConfig

REPO_ROOT = Path(__file__).resolve().parent.parent
fileConfig(f'{REPO_ROOT}/logging.cfg')

from .event_processors import Processor, ConfigEntry
from quart import Quart, request
from quart.wrappers import Response

log = logging.getLogger(__name__)

def uncaught_exception_handler(exctype: Any , value: Any, tb: Any) -> Any:
   log.exception('Uncaught exception', extra={    # pragma: no cover
        'exctype': exctype,
        'value': value,
        'tb': tb
    })
sys.excepthook = uncaught_exception_handler


commit_info = None
if os.path.exists(f'{REPO_ROOT}/git-info.txt'):
    with open(f'{REPO_ROOT}/git-info.txt') as f: # pragma: no cover
        commit_info = ''.join(f.readlines())



def get_processor_list() -> List[ConfigEntry]:
   processor_list = []
   config_file = os.environ.get('GOOSE_CONFIG', '/etc/goose.yaml')
   if os.path.exists(config_file):
      with open(config_file, 'r') as f:
          cfg = yaml.safe_load(f)
      for entry in cfg:
          processor_list.append(
              ConfigEntry(
                  entry['name'],
                  entry['url'],
                  [x for x in entry.get('filePatterns', '') if '*' not in x],
              )
          )
   return processor_list

process = Processor(get_processor_list())

GITHUB_EVENT_NAME_HEADER = 'X-GitHub-Event'
FOUND_WEBHOOK_HEADER = 'did-process'
MATCHED_HEADER = 'did-match-rule'

app = Quart(__name__)

@app.route('/')
async def index() -> str:
    log.info("Index")
    return f"works: {commit_info}"

@app.route('/webhook', methods=['POST'])
async def webhook() -> Response:
    log.info("webhook")
    # TODO: Emit metric on payload size. Github caps events at 25mb.
    event = request.headers.get(GITHUB_EVENT_NAME_HEADER)
    # TODO: hmac validation of incoming payload
    log.info(f"Incoming event: {event}")

    j = await (request.get_json())
    log.debug("incoming JSON payload", extra={"json": json.dumps(j, indent=2)})

    # Dispatch to a method called e.g. process_foo when the event type is "foo".
    p = getattr(process, 'process_{}'.format(event), None)
    log.debug(f'Has method for the {event} event? {p is not None}')
    processed = 'no'
    matched_rule = 'no'
    if p is not None:
        if p((await request.get_json())):
            matched_rule = 'yes'
        processed = 'yes'
    else:
        log.debug(f"Unable to find a handler for event: {event}")
    return Response({}, 200, {
       FOUND_WEBHOOK_HEADER: processed,
       MATCHED_HEADER: matched_rule
    })

if __name__ == '__main__':
    app.run()
