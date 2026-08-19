"""Shared fixtures for the `opus_import` tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from opus_config._secrets_compat import (
    OPUS_SECRETS_ENV_VAR,
    SECRETS_FILENAME,
    load_secrets,
)

SECRETS_SOURCE = "IMPORT_TABLE_TEMP_PREFIX = 'imp_'\n"


@pytest.fixture(autouse=True)
def _secrets_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Point the pipeline at a throwaway secrets file for the duration of one test.

    The pipeline reads its settings through the transitional shim, which memoizes the
    loaded file process-wide; writing a fresh file per test and clearing that cache
    around it keeps one test's settings out of the next one.
    """
    path = tmp_path / SECRETS_FILENAME
    path.write_text(SECRETS_SOURCE)
    monkeypatch.setenv(OPUS_SECRETS_ENV_VAR, str(path))
    load_secrets.cache_clear()
    yield
    load_secrets.cache_clear()
