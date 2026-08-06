import logging
import sys
from contextvars import ContextVar

from app.core.config import settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            if not any(isinstance(f, RequestIdFilter) for f in handler.filters):
                handler.addFilter(RequestIdFilter())
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(RequestIdFilter())
        root.addHandler(handler)
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root.handlers[0].setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(request_id)s | %(message)s"
        )
    )
