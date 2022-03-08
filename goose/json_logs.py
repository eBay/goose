from typing import Any
import logging
from pythonjsonlogger import jsonlogger # type: ignore
from datetime import datetime

class JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Any, record: Any, message_dict: Any) -> None:
        super(JsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
