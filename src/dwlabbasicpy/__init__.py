from importlib.metadata import PackageNotFoundError, version

from .dwlabLogger import DwlabLoggerConfiguration, LoggingConfigurationError, setup_logging
from .dwlabObjectHandler import dictToObject
from .dwlabRuntimeEnvironment import dwlabRuntimeEnvironment
from .dwlabSettings import dwlabSettings
from .dwlabSetup import get_deb_package_version, get_package_version

try:
    __version__ = version("dwlabbasicpy")
except PackageNotFoundError:
    __version__ = "0+unknown"

__all__ = [
    "DwlabLoggerConfiguration",
    "LoggingConfigurationError",
    "dictToObject",
    "dwlabRuntimeEnvironment",
    "dwlabSettings",
    "get_deb_package_version",
    "get_package_version",
    "setup_logging",
    "__version__",
]
