"""Logging setup for the whole application, called once at startup (see app.py).

Every log line shows the id of the HTTP request it belongs to, e.g. [3f9a1c2e], so
the lines of requests served at the same time can be told apart; "-" outside a
request (startup, shutdown). app.py sets the id for each request (request_id_var).
"""

import logging
import uuid
from contextvars import ContextVar

# Id of the HTTP request being served. A ContextVar, so each request (and every task
# it starts, e.g. the RAG graph's nodes) sees its own id, also when many run at once.
request_id_var = ContextVar("request_id", default="-")


def new_request_id():
    """A short random id for one request, e.g. "3f9a1c2e"."""
    return uuid.uuid4().hex[:8]


class RequestIdFilter(logging.Filter):
    """Adds the current request's id to every log record, as record.request_id."""

    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


class ColorFormatter(logging.Formatter):
    """Log formatter that colors the level name: INFO green, WARNING yellow, ERROR red."""

    # ANSI terminal color codes
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[1;31m",
    }
    RESET = "\033[0m"

    def format(self, record):
        # Color a copy of the record, so other handlers still get the plain level name.
        record = logging.makeLogRecord(record.__dict__)
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname:<7}{self.RESET}"
        return super().format(record)


def setup_logging():
    """Log INFO and above to the console, with time, level, request id and module name.
    The level name is colored when the output is a terminal (not a file or a pipe)."""
    log_format = "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler()
    # On the handler, not a logger, so records from every logger get the id.
    handler.addFilter(RequestIdFilter())
    if handler.stream.isatty():
        handler.setFormatter(ColorFormatter(log_format, date_format))
    else:
        handler.setFormatter(logging.Formatter(log_format, date_format))
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    # The HTTP client used by openai logs every request at INFO; only show its warnings.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
