"""Shared fixtures for the `opus_config` tests."""

from collections.abc import Iterator

import pytest

from opus_config._secrets_compat import load_secrets


@pytest.fixture(autouse=True)
def _clear_secrets_cache() -> Iterator[None]:
    """Drop the process-wide secrets cache around every test.

    `load_secrets` memoizes its result, so without this a value loaded by one test
    would leak into the next one.
    """
    load_secrets.cache_clear()
    yield
    load_secrets.cache_clear()
