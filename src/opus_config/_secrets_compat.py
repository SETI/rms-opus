"""Loader for the ``opus_secrets.py`` configuration file.

The import pipeline and the Django backend both read their settings from an
``opus_secrets.py``, which the CI and deployment scripts generate and which a developer
copies from ``opus_secrets_template.py`` and edits by hand. The file is located by path
and executed rather than imported, so it need not be importable and no ``sys.path`` entry
is required to reach it.

Search order:

1. The ``OPUS_SECRETS`` environment variable, an absolute path to the secrets *file*
   (not its directory). Servers hosting several OPUS installs set a distinct value
   per install.
2. ``opus_secrets.py`` in the process's current working directory, which is what the
   CI and deployment scripts produce.
"""

# This module is scaffolding, which is why it is private: it is deleted, together with
# `opus_secrets_template.py`, when `opus_config` grows its TOML loader. Keep the surface
# it exposes to `opus_import` and `opus_app` as small as possible so that swap is cheap.

import functools
import importlib.util
import os
from pathlib import Path
from types import ModuleType

#: Environment variable holding an absolute path to the secrets file.
OPUS_SECRETS_ENV_VAR = 'OPUS_SECRETS'

#: Name looked for in the current working directory when the variable is unset.
SECRETS_FILENAME = 'opus_secrets.py'

_SECRETS_MODULE_NAME = 'opus_secrets'


def secrets_path() -> Path:
    """Return the path the secrets file will be loaded from.

    The path is not checked for existence; `load_secrets` reports a missing file.

    Returns:
        The value of the ``OPUS_SECRETS`` environment variable if it is set and
        non-empty, otherwise ``opus_secrets.py`` in the current working directory.

    Raises:
        ValueError: If ``OPUS_SECRETS`` is set to a relative path. Resolving one
            against the working directory would make the settings a process
            inherits depend on where it happens to have been started, which is
            exactly what naming the file explicitly is meant to prevent.
    """
    env_value = os.environ.get(OPUS_SECRETS_ENV_VAR)
    if env_value:
        path = Path(env_value)
        if not path.is_absolute():
            raise ValueError(f'{OPUS_SECRETS_ENV_VAR} must be an absolute path to the '
                             f'secrets file: {path}')
        return path
    return Path.cwd() / SECRETS_FILENAME


@functools.cache
def load_secrets() -> ModuleType:
    """Load the secrets file and return it as a module.

    The file is executed once per process and the resulting module is cached, so every
    caller sees one set of settings. The module is deliberately *not* registered in
    ``sys.modules``, so a stray ``import opus_secrets`` fails loudly instead of silently
    resolving to this copy.

    Returns:
        The executed secrets module; every setting is an attribute on it.

    Raises:
        ValueError: If ``OPUS_SECRETS`` is set to a relative path.
        FileNotFoundError: If no secrets file exists at `secrets_path`.
        Exception: Whatever the secrets file itself raises while executing.
    """
    path = secrets_path()
    if not path.is_file():
        raise FileNotFoundError(
            f'OPUS secrets file not found: {path}. Set the '
            f'{OPUS_SECRETS_ENV_VAR} environment variable to the absolute path of '
            f'{SECRETS_FILENAME}, or run from the directory that contains it.')

    spec = importlib.util.spec_from_file_location(_SECRETS_MODULE_NAME, path)
    if spec is None or spec.loader is None:  # pragma: no cover - unreachable for a .py file
        raise ImportError(f'Cannot load OPUS secrets file: {path}')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
