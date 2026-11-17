"""The ``OPUS_CONFIG`` file the harness writes for each import run and web application.

Every program a bench command starts reads its configuration from this file, which names
the harness-owned MySQL server (`benchmarks.bench_server`), the schema the program works
on, the holdings it reads, a scratch directory of the run's own for its logs, and the
harness's memcached. ``--import-key`` adds ``[import]`` keys to it (`parse_import_keys`).
"""

from __future__ import annotations

import contextlib
import math
import re
from typing import TYPE_CHECKING

from benchmarks.bench_server import DB_HOST, DB_PASSWORD, DB_USER
from import_tests.tools import build_run

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path


#: The ``[import]`` keys `write_opus_config` sets, which name the logs a run's results
#: are read from, so ``--import-key`` refuses them.
HARNESS_IMPORT_KEYS = ('log_file', 'debug_log_file')


def _import_key_value(text: str) -> object:
    """Return an ``--import-key`` value as the type TOML would give it.

    Parameters:
        text: The value as written.

    Returns:
        A boolean for ``true`` or ``false``, a whole number, a finite decimal number, or
        else the text itself.
    """
    if text in ('true', 'false'):
        return text == 'true'
    with contextlib.suppress(ValueError):
        return int(text)
    with contextlib.suppress(ValueError):
        number = float(text)
        if math.isfinite(number):
            return number
    return text


def parse_import_keys(pairs: Sequence[str]) -> dict[str, object]:
    """Read ``--import-key`` arguments into the ``[import]`` keys they set.

    Parameters:
        pairs: Each ``KEY=VALUE``.

    Returns:
        The keys, each value a whole number, a finite decimal number, a boolean or a
        string, in argument order.

    Raises:
        ValueError: If an argument has no ``=``, or its key is not a TOML bare key, or
            is one of `HARNESS_IMPORT_KEYS`.
    """
    keys: dict[str, object] = {}
    for pair in pairs:
        key, separator, text = pair.partition('=')
        if not separator or not key:
            raise ValueError(f'--import-key takes KEY=VALUE, not {pair!r}')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', key):
            raise ValueError(f'--import-key {pair!r}: {key!r} is not an [import] key name')
        if key in HARNESS_IMPORT_KEYS:
            raise ValueError(
                f'--import-key {pair!r}: the harness sets {key} itself and reads that log'
            )
        keys[key] = _import_key_value(text)
    return keys


def write_opus_config(
    path: Path,
    *,
    schema: str,
    pds3_holdings: Path,
    pds4_holdings: Path,
    run_dir: Path,
    cache_location: str,
    extra_import: Mapping[str, object] | None = None,
) -> Path:
    """Write the ``OPUS_CONFIG`` a harness-run import or web application reads.

    Every directory it names is created under `run_dir`, so each run starts with an
    empty log directory.

    Parameters:
        path: The file to write.
        schema: The schema on the owned server.
        pds3_holdings: The PDS3 holdings root.
        pds4_holdings: The PDS4 holdings root.
        run_dir: The run's own scratch directory.
        cache_location: The owned memcached's ``host:port``.
        extra_import: Further ``[import]`` keys and their values -- an integer, a
            boolean or a string -- or None for none. One the file sets itself
            (``log_file``, ``debug_log_file``) takes this value instead. A side whose
            configuration does not know a key refuses the file, so a session sets one
            only for a side that does.

    Returns:
        The path written.
    """
    log_dir = run_dir / 'logs'
    for directory in (log_dir, run_dir / 'tar', run_dir / 'manifest', run_dir / 'static'):
        directory.mkdir(parents=True, exist_ok=True)

    def toml(value: object) -> str:
        """Return a TOML basic string."""
        return f'"{build_run.toml_string(str(value))}"'

    import_keys: dict[str, object] = {
        'log_file': str(log_dir / 'opus_import.log'),
        'debug_log_file': str(log_dir / 'opus_import_debug.log'),
        **(extra_import or {}),
    }
    lines = [
        '[database]',
        'brand = "MySQL"',
        f'host = {toml(DB_HOST)}',
        'database = ""',
        f'schema = {toml(schema)}',
        f'user = {toml(DB_USER)}',
        f'password = {toml(DB_PASSWORD)}',
        '',
        '[paths]',
        f'pds3_holdings = {toml(pds3_holdings)}',
        f'pds4_holdings = {toml(pds4_holdings)}',
        f'opus_log_file = {toml(log_dir / "opus_log.txt")}',
        f'import_log_dir = {toml(log_dir)}',
        f'tar_dir = {toml(str(run_dir / "tar") + "/")}',
        f'manifest_dir = {toml(str(run_dir / "manifest") + "/")}',
        f'last_blog_update_file = {toml(run_dir / "last_blog_update.txt")}',
        f'notification_file = {toml(run_dir / "notification.html")}',
        f'opus_static_root = {toml(run_dir / "static")}',
        '',
        '[django]',
        'secret_key = "benchmark-harness-throwaway-key"',
        'debug = false',
        'allowed_hosts = ["127.0.0.1", "localhost"]',
        'cache_server_prefix = "benchmarks"',
        f'cache_location = {toml(cache_location)}',
        'public_url = "https://opus.invalid/"',
        'product_http_path = "https://opus.invalid/"',
        'viewmaster_url = "https://viewmaster.invalid/"',
        'tar_file_url = "https://opus.invalid/tar/"',
        'log_file_level = "WARNING"',
        'log_console_level = "WARNING"',
        'log_django_level = "WARNING"',
        '',
        '[import]',
        *(f'{key} = {build_run.toml_value(value)}' for key, value in import_keys.items()),
        '',
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines), encoding='utf-8')
    return path
