"""Configuration for the OPUS import pipeline and the OPUS Django backend.

Both `opus_import` and `opus_app` need configuration and neither may import the other,
so the loader lives in its own tiny package. This package is also where setuptools-scm
writes the distribution's `_version.py`; every other package in the distribution reads
its version through `importlib.metadata.version("rms-opus")`.

Configuration itself is read through `opus_config._secrets_compat`, which is private:
the package exports nothing, and callers import the loader from that module directly.
"""

# `_secrets_compat` is scaffolding. It is replaced wholesale when this package grows
# its TOML loader (`OPUS_CONFIG`, frozen dataclasses, explicit validation), whose
# frozen section objects then become the public surface here, so nothing outside the
# package should grow a dependency on the shim beyond reading settings from it.
__all__: list[str] = []
