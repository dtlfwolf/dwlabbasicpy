from importlib.metadata import PackageNotFoundError, version


def get_package_version(package_name):
    try:
        return version(package_name)
    except PackageNotFoundError:
        return f"Package '{package_name}' is not installed."


def get_deb_package_version(package_name):
    """Backward-compatible alias for callers still using the old helper name."""
    return get_package_version(package_name)
