"""Shared fixtures for the `opus_import` tests."""

import argparse
from pathlib import Path
from typing import Any

import pytest

from opus_config import OPUS_CONFIG_ENV_VAR
from opus_import.context import ImportContext


class RecordingLogger:
    """A `pdslogger.PdsLogger` stand-in that keeps every message instead of writing it."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def log(self, level: str, msg: str, *args: Any, **kwargs: Any) -> None:
        """Record one message.

        Parameters:
            level: The level name the pipeline logged at.
            msg: The formatted message.
            args: Ignored; the pipeline formats its messages before logging them.
            kwargs: Ignored, as `args` is.
        """
        self.messages.append((level, msg))

    def messages_at(self, level: str) -> list[str]:
        """Return every message logged at `level`, in the order they were logged.

        Parameters:
            level: The level name to filter on, such as ``'error'``.

        Returns:
            The messages, oldest first.
        """
        return [msg for msg_level, msg in self.messages if msg_level == level]


def make_context(**kwargs: Any) -> ImportContext:
    """Return an `ImportContext` with a recording logger and no database.

    Parameters:
        kwargs: Fields to override, such as ``db=`` or ``args=``.

    Returns:
        A context whose `ImportContext.logger` is a `RecordingLogger` and whose
        `ImportContext.args` is an empty `argparse.Namespace`, unless overridden.
    """
    kwargs.setdefault('args', argparse.Namespace())
    kwargs.setdefault('logger', RecordingLogger())
    return ImportContext(**kwargs)


@pytest.fixture(autouse=True)
def _opus_config(ci_config_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the pipeline at the checked-in dummy configuration.

    Anything the pipeline reads out of it comes from that one file, so a test asserting
    on a configured value and the CI jobs are looking at the same settings. The
    process-wide cache is cleared around every test by the root conftest.
    """
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(ci_config_path))

