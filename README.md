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
python3 -m build
```

This creates a source distribution and wheel in `dist/`.

## Install

Install into the active Python environment:

```bash
python3 -m pip install .
```

Install from a built wheel:

```bash
python3 -m pip install dist/dwlabbasicpy-0.20.0-py3-none-any.whl
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
