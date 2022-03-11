from typing import Any
from datetime import datetime
from pythonjsonlogger import jsonlogger  # type: ignore


class JsonFormatter(jsonlogger.JsonFormatter):
    '''
    Adds a few specific properties to the json formatter.
    '''

    def add_fields(self, log_record: Any, record: Any, message_dict: Any) -> None:
        super()
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
