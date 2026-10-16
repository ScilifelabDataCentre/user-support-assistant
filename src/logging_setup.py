"""Logging setup for the whole application, called once at startup (see app.py)."""

import logging


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
    """Log INFO and above to the console, with time, level and module name.
    The level name is colored when the output is a terminal (not a file or a pipe)."""
    log_format = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler()
    if handler.stream.isatty():
        handler.setFormatter(ColorFormatter(log_format, date_format))
    else:
        handler.setFormatter(logging.Formatter(log_format, date_format))
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    # The HTTP client used by openai logs every request at INFO; only show its warnings.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
