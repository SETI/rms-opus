"""Configuration for the OPUS import pipeline and the OPUS Django backend.

Both `opus_import` and `opus_app` need configuration and neither may import the other,
so the loader lives in its own tiny package. This package is also where setuptools-scm
writes the distribution's `_version.py`; every other package in the distribution reads
its version through `importlib.metadata.version("rms-opus")`.

An installation is described by one TOML file, found through the ``OPUS_CONFIG``
environment variable. `get_config` reads it once per process and returns an
`OpusConfig`; `load_config` reads a file named directly, which is what a test does.
The schema, and the errors an invalid file produces, are documented in
`opus_config.config`.
"""

from opus_config.config import (
    DATABASE_BRANDS,
    LOG_LEVELS,
    OPUS_CONFIG_ENV_VAR,
    TABLE_NAMES,
    ConfigError,
    DatabaseConfig,
    DjangoConfig,
    ImportConfig,
    OpusConfig,
    PathsConfig,
    config_path,
    get_config,
    load_config,
)

__all__ = [
    'DATABASE_BRANDS',
    'LOG_LEVELS',
    'OPUS_CONFIG_ENV_VAR',
    'TABLE_NAMES',
    'ConfigError',
    'DatabaseConfig',
    'DjangoConfig',
    'ImportConfig',
    'OpusConfig',
    'PathsConfig',
    'config_path',
    'get_config',
    'load_config',
]
