"""Structured operation reporting for DW-Lab command-line applications."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Mapping, Protocol


@dataclass(frozen=True)
class OperationEvent:
    """One lifecycle event emitted by a mutating DW-Lab operation."""

    operation: str
    phase: str
    outcome: str
    context: Mapping[str, str]
    error: str | None = None


class OperationReporter(Protocol):
    """Report deterministic operation lifecycle events."""

    def started(self, operation: str, phase: str, context: Mapping[str, str]) -> None:
        """Report that an operation phase has started."""

    def passed(self, operation: str, phase: str, context: Mapping[str, str]) -> None:
        """Report that an operation phase completed successfully."""

    def failed(self, operation: str, phase: str, context: Mapping[str, str], error: Exception) -> None:
        """Report that an operation phase failed."""


class NullOperationReporter:
    """No-op reporter for library callers that do not require events."""

    def started(self, operation: str, phase: str, context: Mapping[str, str]) -> None:
        pass

    def passed(self, operation: str, phase: str, context: Mapping[str, str]) -> None:
        pass

    def failed(self, operation: str, phase: str, context: Mapping[str, str], error: Exception) -> None:
        pass


class LoggingOperationReporter:
    """Emit operation events through a package logger without polluting stdout."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def started(self, operation: str, phase: str, context: Mapping[str, str]) -> None:
        self._log(OperationEvent(operation, phase, "START", context))

    def passed(self, operation: str, phase: str, context: Mapping[str, str]) -> None:
        self._log(OperationEvent(operation, phase, "PASS", context))

    def failed(self, operation: str, phase: str, context: Mapping[str, str], error: Exception) -> None:
        self._log(OperationEvent(operation, phase, "FAIL", context, str(error)), error=True)

    def _log(self, event: OperationEvent, *, error: bool = False) -> None:
        context = json.dumps(dict(event.context), sort_keys=True)
        message = "STEP %s: operation=%s phase=%s context=%s" % (
            event.outcome,
            event.operation,
            event.phase,
            context,
        )
        if event.error:
            message = f"{message} error={event.error}"
        if error:
            self._logger.error(message)
        else:
            self._logger.info(message)
