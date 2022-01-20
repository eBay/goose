from quart import Quart, request
from event_processors import Processor, ConfigEntry
import logging
import json

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

app = Quart(__name__)

# TODO: per-environment config
process = Processor([{
    'testing': ConfigEntry('http://example.org/url')
}])

GITHUB_EVENT_NAME_HEADER = 'X-GitHub-Event'
FOUND_WEBHOOK_HEADER = 'did-process'

@app.route('/')
async def index():
    log.info("Index")
    return "works"

@app.route('/webhook', methods=['POST'])
async def webhook():
    log.info("webhook")
    # TODO: Emit metric on payload size. Github caps events at 25mb.
    event = request.headers.get(GITHUB_EVENT_NAME_HEADER)
    # TODO: hmac validation of incoming payload
    log.info(f"Incoming event: {event}")

    j = await (request.get_json())
    log.debug(f"JSON: {json.dumps(j, indent=2)}")

    p = getattr(process, 'process_{}'.format(event), None)
    processed = 'no'
    if p is not None:
        # TODO: This should likely be
        p((await request.get_json()))
        processed = 'yes'
    else:
        log.debug(f"Unable to find a handler for event: {event}")


    return {}, 200, {FOUND_WEBHOOK_HEADER: processed}

if __name__ == '__main__':
    app.run()
