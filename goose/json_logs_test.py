from unittest.mock import MagicMock
from .json_logs import JsonFormatter


def test_formatter():
    jf = JsonFormatter()
    record = {}
    record = MagicMock()
    jf.add_fields(record, record, {})
