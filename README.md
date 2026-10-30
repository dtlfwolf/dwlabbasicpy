# dwlabbasicpy

`dwlabbasicpy` provides the shared Python utilities used by DW-Lab packages.
It is now intended to be built and deployed as a standard pip package instead
of a Debian package. The importable Python code uses a `src/` layout.

## Features

- YAML-based logging configuration bootstrap
- DW-Lab runtime environment discovery helpers
- YAML/XML settings serialization helpers
- Small object conversion utilities

## Build

Build standard Python distribution artifacts:

```bash
python3 -m build --no-isolation
```

This creates a source distribution and wheel in `dist/`.

## Install

Install into the active Python environment:

```bash
python3 -m pip install .
```

Install from a built wheel:

```bash
python3 -m pip install dist/dwlabbasicpy-0.22.0-py3-none-any.whl
```

Install into a deployment target directory:

```bash
python3 -m pip install --target /opt/dwlab/python .
```

Install directly from a package index:

```bash
python3 -m pip install dwlabbasicpy
```

For DW-Lab deployments that keep shared Python modules outside the system
interpreter, add the target directory to `PYTHONPATH`:

```bash
export PYTHONPATH=/opt/dwlab/python${PYTHONPATH:+:$PYTHONPATH}
```

## Logging Configuration

At runtime, logging configuration is resolved in this order:

1. An explicit `config_path`
2. `/etc/dwlab/<package_name>/logging.yaml`
3. A caller-adjacent `etc/logging.yaml`
4. The packaged fallback file `dwlabbasicpy/etc/logging.yaml`

This allows pip-installed deployments to work without a Debian package while
still supporting DW-Lab system-wide configuration paths.

### UTC-By-Default Operational Logging

Starting with `0.22.0`, calling `setup_logging()` uses UTC for the packaged
logging configuration and the minimal fallback. This affects only applications
that explicitly request setup. Importing the library does not configure logging.

Select an alternative IANA timezone if required:

```python
from dwlabbasicpy import setup_logging

setup_logging(package_name="my_application")  # UTC by default
# Alternatively, at application startup:
setup_logging(package_name="my_application", timezone="Europe/Berlin")
```

`DwlabLoggerConfiguration` accepts the same keyword-only `timezone` option.
Non-UTC output includes an explicit offset, such as `+01:00` or `+02:00` for
Berlin, with daylight-saving rules applied to the event's timestamp. Invalid
timezone names raise `ValueError`, rather than silently falling back to local
time. The OS must provide IANA timezone data for non-UTC zones. Python 3.8 uses
the declared `backports.zoneinfo` dependency; newer Python uses stdlib `zoneinfo`.

Customer-provided YAML configurations remain authoritative and are not rewritten.
The `timezone` argument controls only built-in/default formatting. To select a
timezone inside customer YAML, use the `dwlabbasicpy.DwlabLogFormatter` factory
with `timezone: Europe/Berlin` (or `UTC`). Existing custom/local-time formatters
remain unchanged until explicitly migrated. Fallback setup also preserves
already configured root handlers, following Python's `basicConfig` semantics.

Starting with `0.21.0`, `UtcLogFormatter` provides RFC 3339 UTC timestamps with
milliseconds and an explicit `Z`, plus host, component and run ID context:

```text
2026-10-29T13:00:05.359Z INFO host="central-01" component="proxy" run_id="run-42" STEP PASS: ready
```

Select it explicitly on an application-owned handler:

```python
import logging
from dwlabbasicpy import UtcLogFormatter

handler = logging.StreamHandler()
handler.setFormatter(UtcLogFormatter(component="proxy", run_id="run-42"))
logger = logging.getLogger("my_application")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False
logger.info("STEP PASS: ready")
```

The application should attach its handler once at startup. Reusable libraries
should only emit records through their logger, not configure application logging.
Importing or constructing the formatter does not modify root loggers, handlers,
record factories, existing formatters or the machine's timezone.
`UtcLogFormatter` remains UTC-only for compatibility. `DwlabLogFormatter`
provides the same context fields with an optional `timezone` constructor argument.

Constructor options `host`, `component` and `run_id` supply context defaults.
When omitted, these use the local hostname, the record's logger name, and `-`,
respectively. Per-event context can override defaults:

```python
logger.info("Client connected", extra={"host": "client-01", "run_id": "run-43"})
```

Context values are JSON-quoted to preserve spaces and escape newlines. Formatting
uses a private copy of each record so other handlers retain its original fields.
Message interpolation, exception tracebacks and `LoggingOperationReporter` work
with the new formatter without changes.

For application YAML configuration, select the formatter through its factory:

```yaml
version: 1
disable_existing_loggers: false
formatters:
  utc:
    (): dwlabbasicpy.UtcLogFormatter
    component: proxy
    run_id: run-42
handlers:
  console:
    class: logging.StreamHandler
    formatter: utc
    stream: ext://sys.stderr
loggers:
  my_application:
    handlers: [console]
    level: INFO
    propagate: false
```

Apply it explicitly with `setup_logging(package_name="my_application",
config_path="/path/to/logging.yaml")`. Run IDs are supplied by the application;
the formatter does not implicitly read environment variables or global context.

This is a shared formatting primitive, not clock synchronization or log ingestion.
It does not convert third-party files, normalize shell logs, or change Checkmk
timezones/schedules. Products and test runners must opt in separately. Measure
elapsed durations using `time.monotonic()` and verify host clock synchronization
independently; UTC formatting alone does not establish accurate event ordering.

### Upgrade, Removal And Verification

Upgrade using `python3 -m pip install --upgrade dwlabbasicpy` or install the new
wheel in the product's own environment. No configuration migration is required.
Remove this formatter selection to return to the application's previous format.
`python3 -m pip uninstall dwlabbasicpy` removes the library; do not uninstall it
from environments where other products depend on it. Bundled deployments must
consume the new wheel through their own independently versioned installers.

Run the package's standalone tests with `python3 -m pytest -q`. UTC formatter
tests cover multiple process timezones, context overrides, shared-record
isolation, exception rendering, operation reporting and YAML formatter factories.
