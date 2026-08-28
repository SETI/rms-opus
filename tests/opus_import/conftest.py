"""Shared fixtures for the `opus_import` tests."""

import argparse
from pathlib import Path
from typing import Any

import pytest

from opus_config import OPUS_CONFIG_ENV_VAR
from opus_import import cli
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


def default_arguments() -> argparse.Namespace:
    """Return what the real command line produces when it is given no options.

    Built by parsing an empty argument list with the pipeline's own parser rather than
    by listing the options a test happens to need. A hand-built namespace holds only
    the options someone remembered, so it stops matching the CLI the moment an option
    is added and any code reading a newer one raises `AttributeError` in the tests
    while working in production -- or, worse, the reverse.

    Returns:
        A namespace carrying every option with its documented default.
    """
    return cli._create_argument_parser().parse_args([])


def make_context(**kwargs: Any) -> ImportContext:
    """Return an `ImportContext` with a recording logger and no database.

    Parameters:
        kwargs: Fields to override, such as ``db=`` or ``args=``.

    Returns:
        A context whose `ImportContext.logger` is a `RecordingLogger` and whose
        `ImportContext.args` is `default_arguments`, unless overridden.
    """
    kwargs.setdefault('args', default_arguments())
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

