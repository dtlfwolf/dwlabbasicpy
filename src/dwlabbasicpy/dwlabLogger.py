import inspect
import logging
import logging.config
from pathlib import Path

import yaml


DEFAULT_CONFIG_FILENAME = "logging.yaml"
DEFAULT_SYSTEM_CONFIG_ROOT = Path("/etc/dwlab")


def _stack_frame(depth, fallback=True):
    stack = inspect.stack()
    if not stack:
        return None
    if depth < len(stack):
        return stack[depth]
    if not fallback:
        return None
    return stack[-1]


class LoggingConfigurationError(RuntimeError):
    """Raised when a discovered logging configuration is unsafe to use."""


class DwlabLoggerConfiguration:
    """Resolve and apply DW-Lab logging configuration for one package/application."""

    def __init__(
        self,
        package_name=None,
        config_path=None,
        default_filename=DEFAULT_CONFIG_FILENAME,
        default_level=logging.INFO,
    ):
        """Initialize logging configuration lookup parameters."""
        self.package_name = package_name
        self.config_path = config_path
        self.default_filename = default_filename
        self.default_level = default_level

    def resolve_package_name(self):
        """Determine the DW-Lab package identifier for the current caller.

        The identifier maps to ``/etc/dwlab/<package_name>/logging.yaml``.
        For pure Python packages this is usually the import package name.
        For mixed bash/python applications this should be the deployed DW-Lab
        application name.

        This remains as a backward-compatible fallback; callers should pass
        package_name explicitly for deterministic lookup behavior.
        """
        if self.package_name:
            return str(self.package_name)

        caller_frame = _stack_frame(3)
        if caller_frame is None:
            return "dwlabbasicpy"

        caller_file = Path(caller_frame.filename).resolve()
        module = getattr(caller_frame, "frame", None)
        module = inspect.getmodule(module) if module is not None else None
        module_package = getattr(module, "__package__", None)
        if module_package:
            return module_package.split(".", 1)[0]

        parts = caller_file.parts
        if "src" in parts:
            index = parts.index("src")
            if index + 1 < len(parts):
                return parts[index + 1]

        if "opt" in parts and "dwlab" in parts:
            index = parts.index("dwlab")
            if index + 1 < len(parts):
                return parts[index + 1]

        for parent in [caller_file.parent, *caller_file.parents]:
            pyproject = parent / "pyproject.toml"
            if pyproject.exists():
                content = pyproject.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("name") and "=" in stripped:
                        return stripped.split("=", 1)[1].strip().strip('"').strip("'")
            setup_py = parent / "setup.py"
            if setup_py.exists():
                return parent.name

        return caller_file.parent.name

    def candidate_config_paths(self):
        """Return logging configuration candidates in deterministic lookup order.

        The primary system location is ``/etc/dwlab/<package_name>/logging.yaml``.
        """
        resolved_package_name = self.resolve_package_name()
        candidates = []
        seen = set()

        def add(path):
            if path is None:
                return
            resolved = Path(path)
            if resolved in seen:
                return
            seen.add(resolved)
            candidates.append(resolved)

        add(Path(self.config_path).expanduser() if self.config_path else None)
        add(DEFAULT_SYSTEM_CONFIG_ROOT / resolved_package_name / self.default_filename)

        caller_frame = _stack_frame(3, fallback=False)
        if caller_frame is not None:
            caller_file = Path(caller_frame.filename).resolve()
            add(caller_file.parent.parent / "etc" / self.default_filename)

        package_root = Path(__file__).resolve().parent
        add(package_root / "etc" / self.default_filename)

        return candidates

    def validate_config_file(self, path):
        """Reject obviously unsafe logging configuration files."""
        stat_result = path.stat()
        if stat_result.st_mode & 0o002:
            raise LoggingConfigurationError(
                f"Logging configuration file '{path}' is world-writable. Refusing to load it."
            )

    def load_logging_config(self, path):
        """Load a YAML logging configuration from the given file path."""
        with path.open("r", encoding="utf-8") as file_handle:
            config = yaml.safe_load(file_handle) or {}
        logging.config.dictConfig(config)

    def configure_fallback(self):
        """Apply a minimal fallback configuration when no YAML file can be used."""
        logging.basicConfig(level=self.default_level)
        return None

    def setup(self):
        """Configure Python logging from the first valid DW-Lab configuration source.

        ``package_name`` is the canonical DW-Lab package or application identifier
        used to resolve ``/etc/dwlab/<package_name>/logging.yaml``.
        """
        candidates = self.candidate_config_paths()
        failures = []

        for candidate in candidates:
            if not candidate.exists():
                continue
            try:
                self.validate_config_file(candidate)
                self.load_logging_config(candidate)
                return str(candidate)
            except Exception as exc:
                failures.append((candidate, exc))
                print(
                    f"Logging configuration file at {candidate} could not be loaded: {exc}. "
                    f"Trying next candidate."
                )
                continue

        if failures:
            checked_paths = ", ".join(str(path) for path, _ in failures)
            print(
                f"No usable logging configuration file found. Checked: {checked_paths}. "
                f"Using default level."
            )
            return self.configure_fallback()

        checked_paths = ", ".join(str(path) for path in candidates)
        print(
            f"Logging configuration file not found. Checked: {checked_paths}. Using default level."
        )
        return self.configure_fallback()


def setup_logging(
    package_name=None,
    config_path=None,
    default_filename=DEFAULT_CONFIG_FILENAME,
    default_level=logging.INFO,
):
    """Compatibility wrapper for OO-based DW-Lab logging setup."""
    return DwlabLoggerConfiguration(
        package_name=package_name,
        config_path=config_path,
        default_filename=default_filename,
        default_level=default_level,
    ).setup()
