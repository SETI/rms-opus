"""Fixtures shared by every OPUS test package."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from opus_config import get_config

#: The dummy configuration the GitHub-hosted CI jobs run against.
CI_CONFIG_PATH = Path(__file__).parent / 'fixtures' / 'opus_ci.toml'


@pytest.fixture(autouse=True)
def _clear_config_cache() -> Iterator[None]:
    """Drop the process-wide configuration cache around every test.

    `opus_config.get_config` reads the file once and keeps the result, so without
    this a configuration loaded by one test would be handed to the next one.
    """
    get_config.cache_clear()
    yield
    get_config.cache_clear()


@pytest.fixture
def ci_config_path() -> Path:
    """Return the path of the checked-in dummy configuration file."""
    return CI_CONFIG_PATH
