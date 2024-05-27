import datetime as dt
import json
import logging
from typing import override


# delete of modify this values
LOG_RECORD_BUILTIN_ATTR = {
    'name': True,
    'levelname': True,
    'levelno': True,
    'pathname': True,
    'lineno': True,
    'funcName': True,
    'exc_info': True,
    'stack_info': True,
    'created': True,
    'formatted': True,
    'args': True,
    'msg': True,
}


class MyJSONFormatter(logging.Formatter):
    def __init__(self, *, fmt_keys: dict[str, str] | None = None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        always_fields = {
            'message': record.getMessage(),
            'timestamp': dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
        }
        if record.exc_info is not None:
            always_fields['exc_info'] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields['stack_info'] = self.formatStack(record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }

        # for extra logs E.g. logger.info('debug message', extra={'x': 'hi'})
        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTR:
                message[key] = val

        return message


class ExactInfoFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == logging.WARNING
