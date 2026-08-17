"""Configuration for the OPUS import pipeline and the OPUS Django backend.

Both `opus_import` and `opus_app` need configuration and neither may import the other,
so the loader lives in its own tiny package.

Today this package holds only the transitional `_secrets_compat` shim, which reads the
legacy `opus_secrets.py` file that the two `sys.path` hacks used to make importable. The
shim's internals are replaced by the real TOML loader (`OPUS_CONFIG`, frozen dataclasses,
explicit validation) later in the modernization sequence, at which point `_secrets_compat`
and `opus_secrets.py` are deleted. Nothing outside this package should grow a dependency
on the shim beyond reading configuration values from it.

This package is also where setuptools-scm writes the distribution's `_version.py`; every
other package in the distribution reads its version through
`importlib.metadata.version("rms-opus")`.
"""
