"""Shared fixtures for the `opus_import` tests."""

from pathlib import Path

import pytest

from opus_config import OPUS_CONFIG_ENV_VAR


@pytest.fixture(autouse=True)
def _opus_config(ci_config_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the pipeline at the checked-in dummy configuration.

    Anything the pipeline reads out of it comes from that one file, so a test asserting
    on a configured value and the CI jobs are looking at the same settings. The
    process-wide cache is cleared around every test by the root conftest.
    """
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(ci_config_path))
