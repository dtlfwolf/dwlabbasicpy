"""Opt-in operational log formatting without application configuration side effects."""

from __future__ import annotations

import copy
from datetime import datetime, timezone as datetime_timezone
import json
import logging
import socket

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # Python 3.8 support.
    from backports.zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class DwlabLogFormatter(logging.Formatter):
    """Format timezone-aware timestamps and correlation context on a chosen handler.

    Context defaults to the local hostname, the record's logger name and ``-``
    for an unspecified run ID. Applications can supply constructor defaults or
    override them per event with ``extra={"host": ..., "component": ...,
    "run_id": ...}``. Context values are JSON-quoted to retain field boundaries
    and escape embedded newlines. No logger, handler or global clock is changed.
    """

    def __init__(
        self,
        *,
        timezone: str = "UTC",
        host: str | None = None,
        component: str | None = None,
        run_id: str | None = None,
    ) -> None:
        """Select UTC or an IANA timezone and store source context defaults."""
        super().__init__(
            "%(asctime)s %(levelname)s host=%(host)s component=%(component)s "
            "run_id=%(run_id)s %(message)s"
        )
        try:
            self._timezone = (
                datetime_timezone.utc if timezone == "UTC" else ZoneInfo(timezone)
            )
        except (ZoneInfoNotFoundError, ValueError, TypeError) as error:
            raise ValueError(f"Invalid logging timezone: {timezone!r}") from error
        self._host = socket.gethostname() if host is None else host
        self._component = component
        self._run_id = "-" if run_id is None else run_id

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """Return RFC 3339 time with milliseconds and an explicit UTC offset.

        ``datefmt`` is intentionally ignored: this formatter always uses its
        documented representation. Formatting does not change event time.
        """
        return datetime.fromtimestamp(record.created, self._timezone).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")

    def format(self, record: logging.LogRecord) -> str:
        """Render a private record copy so other handlers retain original context."""
        local_record = copy.copy(record)
        defaults = {
            "host": self._host,
            "component": self._component if self._component is not None else record.name,
            "run_id": self._run_id,
        }
        for name, default in defaults.items():
            value = getattr(record, name, default)
            setattr(local_record, name, json.dumps(str(value), ensure_ascii=True))
        return super().format(local_record)


class UtcLogFormatter(DwlabLogFormatter):
    """Preserve the explicitly UTC-only formatter API introduced in 0.21.0."""

    def __init__(
        self,
        *,
        host: str | None = None,
        component: str | None = None,
        run_id: str | None = None,
    ) -> None:
        """Always use UTC, irrespective of the host or application timezone."""
        super().__init__(timezone="UTC", host=host, component=component, run_id=run_id)
