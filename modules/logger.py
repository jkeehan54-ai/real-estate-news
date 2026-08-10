# modules/logger.py
# ============================================================
# BRN 2.0 Logger
# Sprint 1-1
# ============================================================

from __future__ import annotations

import logging
import logging.handlers
import sys
import time
from datetime import datetime
from pathlib import Path
from functools import wraps
from typing import Any, Callable, Iterable

from .config import (
    LOG_DIR,
    LOG_LEVEL,
    LOG_ENCODING,
    LOG_CONSOLE,
    LOG_FILE,
)

# ============================================================
# LOG LEVEL
# ============================================================

_LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

LOGLEVEL = _LEVEL_MAP.get(
    str(LOG_LEVEL).upper(),
    logging.INFO,
)

# ============================================================
# DIRECTORY
# ============================================================

LOG_DIR = Path(LOG_DIR)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# ============================================================
# FILE NAME
# ============================================================

TODAY = datetime.now().strftime("%Y%m%d")

MAIN_LOG = LOG_DIR / f"brn_{TODAY}.log"

ERROR_LOG = LOG_DIR / f"error_{TODAY}.log"

RSS_LOG = LOG_DIR / f"rss_{TODAY}.log"

MARKET_LOG = LOG_DIR / f"market_{TODAY}.log"

REPORT_LOG = LOG_DIR / f"report_{TODAY}.log"

HISTORY_LOG = LOG_DIR / f"history_{TODAY}.log"

# ============================================================
# FORMAT
# ============================================================

DEFAULT_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)-18s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

FORMATTER = logging.Formatter(
    DEFAULT_FORMAT,
    DATE_FORMAT,
)

# ============================================================
# HANDLER
# ============================================================

def _file_handler(
    filename: Path,
) -> logging.Handler:

    handler = logging.handlers.RotatingFileHandler(
        filename,
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding=LOG_ENCODING,
    )

    handler.setFormatter(FORMATTER)

    handler.setLevel(LOGLEVEL)

    return handler


def _console_handler() -> logging.Handler:

    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setFormatter(
        FORMATTER
    )

    handler.setLevel(
        LOGLEVEL
    )

    return handler


# ============================================================
# LOGGER FACTORY
# ============================================================

_CREATED: dict[str, logging.Logger] = {}


def get_logger(
    name: str,
    logfile: Path | None = None,
) -> logging.Logger:

    if name in _CREATED:
        return _CREATED[name]

    logger = logging.getLogger(name)

    logger.setLevel(
        LOGLEVEL
    )

    logger.propagate = False

    if LOG_FILE:

        logger.addHandler(
            _file_handler(
                logfile or MAIN_LOG
            )
        )

    if LOG_CONSOLE:

        logger.addHandler(
            _console_handler()
        )

    _CREATED[name] = logger

    return logger


# ============================================================
# COMMON LOGGERS
# ============================================================

main_logger = get_logger(
    "BRN",
    MAIN_LOG,
)

rss_logger = get_logger(
    "RSS",
    RSS_LOG,
)

market_logger = get_logger(
    "MARKET",
    MARKET_LOG,
)

report_logger = get_logger(
    "REPORT",
    REPORT_LOG,
)

history_logger = get_logger(
    "HISTORY",
    HISTORY_LOG,
)

error_logger = get_logger(
    "ERROR",
    ERROR_LOG,
)


# ============================================================
# SAFE MESSAGE
# ============================================================

def _safe_message(
    message: Any,
) -> str:

    try:
        return str(message)

    except Exception:
        return "<unprintable>"


# ============================================================
# BASIC LOGGING
# ============================================================

def debug(
    message: Any,
) -> None:

    main_logger.debug(
        _safe_message(message)
    )


def info(
    message: Any,
) -> None:

    main_logger.info(
        _safe_message(message)
    )


def warning(
    message: Any,
) -> None:

    main_logger.warning(
        _safe_message(message)
    )


def error(
    message: Any,
) -> None:

    error_logger.error(
        _safe_message(message)
    )


def critical(
    message: Any,
) -> None:

    error_logger.critical(
        _safe_message(message)
    )


def exception(
    exc: Exception,
    *,
    logger: logging.Logger = error_logger,
) -> None:

    logger.exception(
        "%s",
        exc,
    )


# ============================================================
# MODULE LOGGING
# ============================================================

def rss(
    message: Any,
) -> None:

    rss_logger.info(
        _safe_message(message)
    )


def market(
    message: Any,
) -> None:

    market_logger.info(
        _safe_message(message)
    )


def report(
    message: Any,
) -> None:

    report_logger.info(
        _safe_message(message)
    )


def history(
    message: Any,
) -> None:

    history_logger.info(
        _safe_message(message)
    )


# ============================================================
# EXECUTION TIMER
# ============================================================

def log_execution(
    logger: logging.Logger = main_logger,
) -> Callable:

    def decorator(
        func: Callable,
    ):

        @wraps(func)
        def wrapper(
            *args,
            **kwargs,
        ):

            start = time.perf_counter()

            logger.info(
                "[START] %s",
                func.__name__,
            )

            try:

                result = func(
                    *args,
                    **kwargs,
                )

                elapsed = (
                    time.perf_counter()
                    - start
                )

                logger.info(
                    "[DONE ] %s (%.3fs)",
                    func.__name__,
                    elapsed,
                )

                return result

            except Exception:

                elapsed = (
                    time.perf_counter()
                    - start
                )

                logger.exception(
                    "[FAIL ] %s (%.3fs)",
                    func.__name__,
                    elapsed,
                )

                raise

        return wrapper

    return decorator


# ============================================================
# LOG TIMER
# ============================================================

class LogTimer:
    """
    실행시간 측정용 Context Manager

    사용 예:
        with LogTimer("RSS 수집"):
            ...
    """

    def __init__(
        self,
        title: str,
        logger: logging.Logger = main_logger,
    ):

        self.title = title

        self.logger = logger

        self.start = 0.0

    def __enter__(self):

        self.start = time.perf_counter()

        self.logger.info(
            "[BEGIN] %s",
            self.title,
        )

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):

        elapsed = (
            time.perf_counter()
            - self.start
        )

        if exc is None:

            self.logger.info(
                "[ END ] %s (%.3fs)",
                self.title,
                elapsed,
            )

        else:

            self.logger.exception(
                "[ERROR] %s (%.3fs)",
                self.title,
                elapsed,
            )

        return False


# ============================================================
# DISPLAY HELPERS
# ============================================================

def banner(
    title: str,
    *,
    logger: logging.Logger = main_logger,
) -> None:

    line_text = "=" * 72

    logger.info(
        line_text
    )

    logger.info(
        title
    )

    logger.info(
        line_text
    )


def section(
    title: str,
    *,
    logger: logging.Logger = main_logger,
) -> None:

    logger.info("")

    logger.info(
        "-" * 60
    )

    logger.info(
        title
    )

    logger.info(
        "-" * 60
    )


def table(
    rows: Iterable[tuple],
    *,
    logger: logging.Logger = main_logger,
) -> None:

    for row in rows:

        text = " | ".join(
            str(value)
            for value in row
        )

        logger.info(
            text
        )


def line(
    char: str = "-",
    length: int = 60,
    *,
    logger: logging.Logger = main_logger,
) -> None:

    logger.info(
        char * length
    )


def blank(
    *,
    logger: logging.Logger = main_logger,
) -> None:

    logger.info("")


# ============================================================
# SHUTDOWN
# ============================================================

def shutdown() -> None:

    logging.shutdown()


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    "get_logger",

    "main_logger",
    "rss_logger",
    "market_logger",
    "report_logger",
    "history_logger",
    "error_logger",

    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "exception",

    "rss",
    "market",
    "report",
    "history",

    "log_execution",
    "LogTimer",

    "banner",
    "section",
    "table",
    "line",
    "blank",

    "shutdown",

]


# ============================================================
# STARTUP
# ============================================================

banner(
    "BRN 2.0 Logger initialized"
)

info(
    "Logging system is ready."
)
