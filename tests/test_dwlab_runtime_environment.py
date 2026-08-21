import importlib
from pathlib import Path
from types import SimpleNamespace

runtime_module = importlib.import_module("dwlabbasicpy.dwlabRuntimeEnvironment")


def _patch_identity(monkeypatch):
    for name in ("DWLAB_HOME", "DWLAB_PACKAGE_ROOT", "DWLAB_SETUP_ROOT", "DWLAB_PACKAGE_NAME"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(runtime_module.socket, "gethostname", lambda: "test-host")
    monkeypatch.setattr(runtime_module.socket, "getfqdn", lambda: "test-host.example.org")
    monkeypatch.setattr(runtime_module.socket, "gethostbyname", lambda hostname: "127.0.0.1")


def _patch_caller(monkeypatch, caller_file):
    fake_stack = [None, SimpleNamespace(filename=str(caller_file))]
    monkeypatch.setattr(runtime_module.inspect, "stack", lambda: fake_stack)


def test_runtime_environment_prefers_dwlab_env_variables(monkeypatch, tmp_path):
    _patch_identity(monkeypatch)
    caller_file = tmp_path / "caller" / "module.py"
    caller_file.parent.mkdir(parents=True)
    caller_file.write_text("# caller\n", encoding="utf-8")
    _patch_caller(monkeypatch, caller_file)

    package_root = tmp_path / "runtime-root" / "dwlab-cmkcentralserver"
    dwlab_home = tmp_path / "runtime-root"
    monkeypatch.setenv("DWLAB_PACKAGE_ROOT", str(package_root))
    monkeypatch.setenv("DWLAB_HOME", str(dwlab_home))
    monkeypatch.setenv("DWLAB_PACKAGE_NAME", "dwlab-cmkcentralserver")

    env = runtime_module.dwlabRuntimeEnvironment()

    assert env.dwlab_package_home == package_root
    assert env.dwlab_home == dwlab_home
    assert env.dwlab_package == "dwlab-cmkcentralserver"


def test_runtime_environment_explicit_arguments_override_env(monkeypatch, tmp_path):
    _patch_identity(monkeypatch)
    caller_file = tmp_path / "caller" / "module.py"
    caller_file.parent.mkdir(parents=True)
    caller_file.write_text("# caller\n", encoding="utf-8")
    _patch_caller(monkeypatch, caller_file)

    monkeypatch.setenv("DWLAB_PACKAGE_ROOT", str(tmp_path / "env-package"))
    monkeypatch.setenv("DWLAB_HOME", str(tmp_path / "env-home"))
    monkeypatch.setenv("DWLAB_PACKAGE_NAME", "env-package")

    explicit_home = tmp_path / "explicit-home"
    explicit_package_home = explicit_home / "explicit-package"
    explicit_src_home = explicit_package_home / "src" / "pkg"

    env = runtime_module.dwlabRuntimeEnvironment(
        dwlab_src_home=explicit_src_home,
        dwlab_package_home=explicit_package_home,
        dwlab_package="explicit-package",
        dwlab_home=explicit_home,
    )

    assert env.dwlab_src_home == explicit_src_home
    assert env.dwlab_package_home == explicit_package_home
    assert env.dwlab_package == "explicit-package"
    assert env.dwlab_home == explicit_home


def test_runtime_environment_keeps_inferred_home_when_default_differs(monkeypatch, tmp_path):
    _patch_identity(monkeypatch)
    inferred_home = tmp_path / "custom-root"
    caller_file = inferred_home / "demo-package" / "src" / "module.py"
    caller_file.parent.mkdir(parents=True)
    caller_file.write_text("# caller\n", encoding="utf-8")
    _patch_caller(monkeypatch, caller_file)
    monkeypatch.setattr(runtime_module, "__DWLAB_HOME__", Path("/opt/dwlab"))

    env = runtime_module.dwlabRuntimeEnvironment(
        dwlab_package_home=inferred_home / "demo-package",
        dwlab_package="demo-package",
    )

    assert env.dwlab_home == inferred_home


def test_runtime_environment_from_dict_preserves_explicit_home(monkeypatch, tmp_path):
    _patch_identity(monkeypatch)
    env_dict = {
        "dwlab_src_home": str(tmp_path / "src"),
        "dwlab_package_home": str(tmp_path / "package"),
        "dwlab_package": "demo-package",
        "dwlab_home": str(tmp_path / "dwlab-home"),
        "hostname": "test-host",
        "fqdn": "test-host.example.org",
        "hostIP": "127.0.0.1",
    }

    env = runtime_module.dwlabRuntimeEnvironment.from_dict(env_dict)

    assert env.dwlab_home == tmp_path / "dwlab-home"
    assert env.dwlab_package_home == tmp_path / "package"
