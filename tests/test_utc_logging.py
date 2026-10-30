"""Verify opt-in UTC formatting and compatibility with ordinary logging."""

import io
import logging
import logging.config
import os
from pathlib import Path
import subprocess
import sys

import pytest

from dwlabbasicpy import DwlabLogFormatter, LoggingOperationReporter, UtcLogFormatter


class TestUtcLogFormatter:
    def record(self, **context):
        record = logging.LogRecord("example.worker", logging.INFO, __file__, 1,
                                   "STEP PASS: %s", ("ready",), None)
        record.created = 0.125
        record.__dict__.update(context)
        return record

    def test_utc_milliseconds_and_constructor_context(self):
        text = UtcLogFormatter(host="central", component="proxy", run_id="run-1").format(
            self.record()
        )
        assert text == (
            '1970-01-01T00:00:00.125Z INFO host="central" component="proxy" '
            'run_id="run-1" STEP PASS: ready'
        )

    def test_defaults_use_hostname_logger_name_and_unspecified_run(self, monkeypatch):
        monkeypatch.setattr("dwlabbasicpy.dwlabLogging.socket.gethostname", lambda: "client")
        text = UtcLogFormatter().format(self.record())
        assert 'host="client" component="example.worker" run_id="-"' in text

    def test_record_context_overrides_defaults_without_mutating_shared_record(self):
        record = self.record(host="remote", component="worker", run_id="event-2")
        before = record.__dict__.copy()
        text = UtcLogFormatter(host="local", run_id="default").format(record)
        assert 'host="remote" component="worker" run_id="event-2"' in text
        assert record.__dict__ == before
        ordinary = logging.Formatter("%(host)s %(message)s").format(record)
        assert ordinary == "remote STEP PASS: ready"

    def test_context_newlines_and_quotes_are_escaped(self):
        text = UtcLogFormatter(host='client\n"other"').format(self.record())
        assert 'host="client\\n\\"other\\""' in text
        assert "\n" not in text

    def test_exception_traceback_is_retained(self):
        try:
            raise ValueError("broken")
        except ValueError:
            record = self.record()
            record.exc_info = sys.exc_info()
        text = UtcLogFormatter().format(record)
        assert "Traceback (most recent call last)" in text
        assert "ValueError: broken" in text
        assert record.exc_text is None

    def test_formatter_can_be_selected_with_dictconfig_factory(self):
        formatter = logging.config.DictConfigurator({}).configure_formatter({
            "()": "dwlabbasicpy.UtcLogFormatter", "host": "configured", "run_id": "run-2",
        })
        assert 'host="configured"' in formatter.format(self.record())

    def test_operation_reporter_uses_formatter_without_reporter_changes(self):
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(UtcLogFormatter(host="central", run_id="run-3"))
        logger = logging.Logger("operations", level=logging.INFO)
        logger.addHandler(handler)
        LoggingOperationReporter(logger).passed("configure", "validate", {})
        assert 'component="operations" run_id="run-3" STEP PASS:' in output.getvalue()

    @pytest.mark.parametrize(
        "timezone", ["UTC", "Europe/Berlin", "America/New_York", "Asia/Tokyo"]
    )
    def test_timezone_does_not_affect_output_or_global_logging(self, timezone):
        source = Path(__file__).resolve().parents[1] / "src"
        code = """
import logging
import time
if hasattr(time, 'tzset'):
    time.tzset()
root = logging.getLogger()
before = (list(root.handlers), root.level, logging.getLogRecordFactory())
from dwlabbasicpy import UtcLogFormatter
formatter = UtcLogFormatter(host='test')
assert before == (list(root.handlers), root.level, logging.getLogRecordFactory())
record = logging.LogRecord('test', logging.INFO, '', 0, 'message', (), None)
record.created = 1793278805.359
print(formatter.format(record))
"""
        result = subprocess.run(
            [sys.executable, "-c", code], check=True, capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": str(source), "TZ": timezone},
        )
        assert result.stdout.startswith("2026-10-29T13:00:05.359Z INFO ")

    @pytest.mark.parametrize("timestamp, offset", [
        (1793278805.359, "+01:00"), (1782738005.359, "+02:00"),
    ])
    def test_explicit_timezone_includes_correct_seasonal_offset(self, timestamp, offset):
        record = self.record()
        record.created = timestamp
        text = DwlabLogFormatter(timezone="Europe/Berlin").format(record)
        assert text.split()[0].endswith(offset)

    def test_general_formatter_defaults_to_utc(self):
        assert DwlabLogFormatter(host="test").format(self.record()).startswith(
            "1970-01-01T00:00:00.125Z "
        )

    def test_invalid_timezone_is_explicitly_rejected(self):
        with pytest.raises(ValueError, match="Invalid logging timezone"):
            DwlabLogFormatter(timezone="Not/AZone")
