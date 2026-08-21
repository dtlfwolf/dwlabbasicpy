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
