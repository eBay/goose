from quart import Quart, request
from event_processors import Processor
import logging

log = logging.getLogger(__name__)

app = Quart(__name__)
process = Processor('') # TODO: Config

GITHUB_EVENT_NAME_HEADER = 'X-GitHub-Event'
FOUND_WEBHOOK_HEADER = 'did-process'

@app.route('/')
async def index():
    return {'works': True}

@app.route('/webhook', methods=['POST'])
async def webhook():
    # TODO: Emit metric on payload size. Github caps events at 25mb.
    event = request.headers[GITHUB_EVENT_NAME_HEADER]
    # TODO: hmac validation of incoming payload
    log.info("Incoming event: {}", event)

    p = getattr(process, 'process_{}'.format(event), None)
    processed = False
    if p is not None:
        p((await request.get_json()))
        processed = True

    return {}, 200, {FOUND_WEBHOOK_HEADER: processed}

if __name__ == '__main__':
    app.run()
