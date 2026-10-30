import logging

from dwlabbasicpy.dwlabOperation import LoggingOperationReporter


def test_logging_reporter_emits_lifecycle_events(caplog) -> None:
    reporter = LoggingOperationReporter(logging.getLogger("dwlabbasicpy.operation-test"))

    with caplog.at_level(logging.INFO):
        reporter.started("test-operation", "validate", {"resource": "example"})
        reporter.passed("test-operation", "validate", {"resource": "example"})
        reporter.failed("test-operation", "activate", {"resource": "example"}, RuntimeError("activation failed"))

    assert "STEP START: operation=test-operation phase=validate" in caplog.text
    assert "STEP PASS: operation=test-operation phase=validate" in caplog.text
    assert "STEP FAIL: operation=test-operation phase=activate" in caplog.text
    assert "error=activation failed" in caplog.text
