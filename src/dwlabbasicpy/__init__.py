from importlib.metadata import PackageNotFoundError, version

from .dwlabLogger import DwlabLoggerConfiguration, LoggingConfigurationError, setup_logging
from .dwlabLogging import DwlabLogFormatter, UtcLogFormatter
from .dwlabOperation import LoggingOperationReporter, NullOperationReporter, OperationEvent, OperationReporter
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
    "DwlabLogFormatter",
    "LoggingConfigurationError",
    "LoggingOperationReporter",
    "NullOperationReporter",
    "OperationEvent",
    "OperationReporter",
    "UtcLogFormatter",
    "dictToObject",
    "dwlabRuntimeEnvironment",
    "dwlabSettings",
    "get_deb_package_version",
    "get_package_version",
    "setup_logging",
    "__version__",
]
