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


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the option that rewrites the obs field-value fixture.

    It lives in the root conftest rather than beside the test that reads it because
    pytest parses the command line before descending into a package, so an option
    declared in `tests/opus_import/conftest.py` is rejected outright by a bare
    ``pytest --regenerate-obs-values`` from the repository root -- the exact
    invocation the fixture's regeneration workflow depends on.

    Parameters:
        parser: The pytest command-line parser.
    """
    parser.addoption('--regenerate-obs-values', action='store_true', default=False,
                     help='Rewrite tests/opus_import/fixtures/obs_field_values.json '
                          'from what the obs classes currently produce.')
