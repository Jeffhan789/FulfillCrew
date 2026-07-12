"""Structured logging for FulfillCrew.

Uses structlog for JSON output when available; falls back to stdlib logging.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 1. Try to import structlog; if unavailable, use a lightweight fallback
# ---------------------------------------------------------------------------

try:
    import structlog

    _STRUCTLOG_AVAILABLE = True
except ImportError:  # pragma: no cover
    _STRUCTLOG_AVAILABLE = False
    structlog = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# 2.  Logging configuration
# ---------------------------------------------------------------------------

def _configure_structlog() -> None:
    """Configure structlog with JSON renderer for production observability."""
    if not structlog:
        return
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _get_fallback_logger(name: str) -> Any:
    """Return a fallback logger-like object that supports keyword arguments.

    When structlog is unavailable, we wrap stdlib logging so that calls like
    ``logger.info("event", key=value)`` do not raise TypeError.
    """

    class _FallbackLogger:
        def __init__(self, name: str) -> None:
            self._log = logging.getLogger(name)
            # Default level: INFO (can be overridden via env var)
            self._log.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            fmt = logging.Formatter(
                "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
            )
            handler.setFormatter(fmt)
            if not self._log.handlers:
                self._log.addHandler(handler)

        def _log_with_kwargs(self, level: int, event: str, **kwargs: Any) -> None:
            if kwargs:
                extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
                self._log.log(level, "%s | %s", event, extra)
            else:
                self._log.log(level, "%s", event)

        def debug(self, event: str, **kwargs: Any) -> None:
            self._log_with_kwargs(logging.DEBUG, event, **kwargs)

        def info(self, event: str, **kwargs: Any) -> None:
            self._log_with_kwargs(logging.INFO, event, **kwargs)

        def warning(self, event: str, **kwargs: Any) -> None:
            self._log_with_kwargs(logging.WARNING, event, **kwargs)

        def error(self, event: str, **kwargs: Any) -> None:
            self._log_with_kwargs(logging.ERROR, event, **kwargs)

        def exception(self, event: str, **kwargs: Any) -> None:
            if kwargs:
                extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
                self._log.exception("%s | %s", event, extra)
            else:
                self._log.exception("%s", event)

    return _FallbackLogger(name)


# ---------------------------------------------------------------------------
# 3.  Public logger instance
# ---------------------------------------------------------------------------

if _STRUCTLOG_AVAILABLE:
    _configure_structlog()
    logger = structlog.get_logger("fulfillcrew")  # type: ignore[union-attr]
else:
    logger = _get_fallback_logger("fulfillcrew")

__all__ = ["logger"]
