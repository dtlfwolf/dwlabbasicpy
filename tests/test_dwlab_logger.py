from pathlib import Path
from types import SimpleNamespace

import pytest

from dwlabbasicpy import dwlabLogger


def test_candidate_config_paths_prefers_explicit_then_system_then_caller_then_packaged(
    monkeypatch, tmp_path
):
    explicit_path = tmp_path / "explicit-logging.yaml"
    config = dwlabLogger.DwlabLoggerConfiguration(
        package_name="demo-package",
        config_path=explicit_path,
    )
    caller_file = tmp_path / "app" / "module.py"
    caller_file.parent.mkdir()
    caller_file.write_text("# test caller\n", encoding="utf-8")

    fake_stack = [None, None, None, SimpleNamespace(filename=str(caller_file))]
    monkeypatch.setattr(dwlabLogger.inspect, "stack", lambda: fake_stack)

    candidates = config.candidate_config_paths()

    assert candidates[0] == explicit_path
    assert candidates[1] == Path("/etc/dwlab/demo-package/logging.yaml")
    assert candidates[2] == tmp_path / "etc" / "logging.yaml"
    assert candidates[3] == (
        Path(dwlabLogger.__file__).resolve().parent / "etc" / "logging.yaml"
    )


def test_setup_uses_packaged_logging_config_as_final_fallback(monkeypatch, tmp_path):
    loaded_paths = []
    system_root = tmp_path / "system"

    monkeypatch.setattr(dwlabLogger, "DEFAULT_SYSTEM_CONFIG_ROOT", system_root)

    def fake_load(self, path):
        loaded_paths.append(path)

    monkeypatch.setattr(
        dwlabLogger.DwlabLoggerConfiguration,
        "load_logging_config",
        fake_load,
    )

    config = dwlabLogger.DwlabLoggerConfiguration(package_name="demo-package")

    selected_path = config.setup()
    packaged_path = Path(dwlabLogger.__file__).resolve().parent / "etc" / "logging.yaml"

    assert selected_path == str(packaged_path)
    assert loaded_paths == [packaged_path]


def test_setup_rejects_world_writable_config_and_uses_next_candidate(
    monkeypatch, tmp_path, capsys
):
    explicit_path = tmp_path / "logging.yaml"
    explicit_path.write_text("version: 1\n", encoding="utf-8")
    explicit_path.chmod(0o666)

    loaded_paths = []
    system_root = tmp_path / "system"

    monkeypatch.setattr(dwlabLogger, "DEFAULT_SYSTEM_CONFIG_ROOT", system_root)

    def fake_load(self, path):
        loaded_paths.append(path)

    monkeypatch.setattr(
        dwlabLogger.DwlabLoggerConfiguration,
        "load_logging_config",
        fake_load,
    )

    config = dwlabLogger.DwlabLoggerConfiguration(
        package_name="demo-package",
        config_path=explicit_path,
    )

    selected_path = config.setup()
    packaged_path = Path(dwlabLogger.__file__).resolve().parent / "etc" / "logging.yaml"
    output = capsys.readouterr().out

    assert "world-writable" in output
    assert selected_path == str(packaged_path)
    assert loaded_paths == [packaged_path]


def test_setup_falls_back_when_no_candidate_exists(monkeypatch, tmp_path):
    fallback_calls = []
    system_root = tmp_path / "system"

    monkeypatch.setattr(dwlabLogger, "DEFAULT_SYSTEM_CONFIG_ROOT", system_root)
    monkeypatch.setattr(
        dwlabLogger.DwlabLoggerConfiguration,
        "configure_fallback",
        lambda self: fallback_calls.append(self.default_level) or None,
    )
    monkeypatch.setattr(
        dwlabLogger,
        "__file__",
        str(tmp_path / "pkg" / "dwlabLogger.py"),
    )

    config = dwlabLogger.DwlabLoggerConfiguration(
        package_name="demo-package",
        config_path=tmp_path / "missing.yaml",
    )

    selected_path = config.setup()

    assert selected_path is None
    assert fallback_calls == [config.default_level]


def test_candidate_config_paths_handles_short_stack(monkeypatch):
    monkeypatch.setattr(
        dwlabLogger.inspect,
        "stack",
        lambda: [SimpleNamespace(filename=str(Path(dwlabLogger.__file__).resolve()))],
    )

    config = dwlabLogger.DwlabLoggerConfiguration(package_name="demo-package")

    candidates = config.candidate_config_paths()

    assert candidates[0] == Path("/etc/dwlab/demo-package/logging.yaml")
    assert candidates[-1] == (
        Path(dwlabLogger.__file__).resolve().parent / "etc" / "logging.yaml"
    )


@pytest.mark.parametrize("timezone", ["UTC", "Europe/Berlin"])
def test_packaged_configuration_uses_selected_timezone(monkeypatch, timezone):
    applied = []
    monkeypatch.setattr(dwlabLogger.logging.config, "dictConfig", applied.append)
    config = dwlabLogger.DwlabLoggerConfiguration(timezone=timezone)
    config.load_logging_config(
        Path(dwlabLogger.__file__).resolve().parent / "etc" / "logging.yaml"
    )
    for formatter in applied[0]["formatters"].values():
        assert formatter["()"] == "dwlabbasicpy.DwlabLogFormatter"
        assert formatter["timezone"] == timezone


def test_customer_formatter_is_not_rewritten(monkeypatch, tmp_path):
    applied = []
    monkeypatch.setattr(dwlabLogger.logging.config, "dictConfig", applied.append)
    path = tmp_path / "logging.yaml"
    path.write_text(
        "version: 1\nformatters:\n  customer:\n"
        "    (): dwlabbasicpy.DwlabLogFormatter\n    timezone: Asia/Tokyo\n"
    )
    dwlabLogger.DwlabLoggerConfiguration(timezone="Europe/Berlin").load_logging_config(path)
    assert applied[0]["formatters"]["customer"]["timezone"] == "Asia/Tokyo"
    assert "timezone: Asia/Tokyo" in path.read_text()


@pytest.mark.parametrize("timezone, suffix", [("UTC", "Z"), ("Europe/Berlin", "+01:00")])
def test_fallback_handler_uses_selected_timezone(monkeypatch, timezone, suffix):
    applied = []
    monkeypatch.setattr(dwlabLogger.logging, "basicConfig", lambda **kw: applied.append(kw))
    dwlabLogger.DwlabLoggerConfiguration(timezone=timezone).configure_fallback()
    record = dwlabLogger.logging.LogRecord("test", 20, "", 0, "ready", (), None)
    record.created = 1793278805.359
    formatter = applied[0]["handlers"][0].formatter
    assert formatter.format(record).split()[0].endswith(suffix)


def test_setup_wrapper_forwards_timezone(monkeypatch):
    monkeypatch.setattr(dwlabLogger.DwlabLoggerConfiguration, "setup", lambda self: self.timezone)
    assert dwlabLogger.setup_logging() == "UTC"
    assert dwlabLogger.setup_logging(timezone="Asia/Tokyo") == "Asia/Tokyo"


def test_invalid_setup_timezone_does_not_apply_configuration(monkeypatch):
    applied = []
    monkeypatch.setattr(dwlabLogger.logging.config, "dictConfig", applied.append)
    with pytest.raises(ValueError, match="Invalid logging timezone"):
        dwlabLogger.setup_logging(timezone="Not/AZone")
    assert not applied
