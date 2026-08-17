"""Transitional loader for the legacy ``opus_secrets.py`` configuration file.

Until the TOML configuration lands, both the import pipeline and the Django backend still
read their settings from a hand-written ``opus_secrets.py``. That file used to be found by
inserting the repository root into ``sys.path`` and doing ``from opus_secrets import *``.
Those inserts are gone, so the file is now located explicitly and executed by path.

Search order:

1. The ``OPUS_SECRETS`` environment variable, an absolute path to the secrets *file*
   (not its directory). Servers that host several OPUS installs set a distinct value
   per install.
2. ``opus_secrets.py`` in the process's current working directory, which is what the
   existing CI and deployment scripts produce.

This module is private and short-lived: it is deleted, together with
``opus_secrets_template.py``, when `opus_config` grows its real TOML loader.
"""

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
    """
    env_value = os.environ.get(OPUS_SECRETS_ENV_VAR)
    if env_value:
        return Path(env_value)
    return Path.cwd() / SECRETS_FILENAME


@functools.cache
def load_secrets() -> ModuleType:
    """Load the legacy secrets file and return it as a module.

    The file is executed once per process and the resulting module is cached, matching
    the semantics of the ``import opus_secrets`` it replaces. The module is deliberately
    *not* registered in ``sys.modules``, so a stray ``import opus_secrets`` still fails
    loudly instead of silently working.

    Returns:
        The executed secrets module; every setting is an attribute on it.

    Raises:
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
