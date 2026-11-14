"""The hold an importer makes at the ``hold_before_lock`` fault site.

The module's clock is replaced by one whose sleep advances it and can act, standing in
for the test that removes the file, so no case depends on threads or wall-clock time.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from opus_import import import_processes


class _Clock:
    """Stands in for the `time` module: `sleep` advances `monotonic` and calls a hook."""

    def __init__(self, on_sleep: Callable[[_Clock], None] | None = None) -> None:
        self.now = 0.0
        self.sleeps = 0
        self.on_sleep = on_sleep

    def monotonic(self) -> float:
        """The simulated time."""
        return self.now

    def sleep(self, seconds: float) -> None:
        """Advance the simulated time, count the sleep, and call the hook."""
        self.now += seconds
        self.sleeps += 1
        if self.on_sleep is not None:
            self.on_sleep(self)


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    """Replace the module's clock."""
    stand_in = _Clock()
    monkeypatch.setattr(import_processes, 'time', stand_in)
    return stand_in


def test_no_file_holds_nothing(tmp_path: Path, clock: _Clock) -> None:
    """An absent file lets the importer go on without sleeping."""
    import_processes.hold_while_present(str(tmp_path / 'absent'), limit=5.0)
    assert clock.sleeps == 0


def test_removing_the_file_ends_the_hold(tmp_path: Path, clock: _Clock) -> None:
    """The hold ends at the first look after the file goes, well inside the limit."""
    hold_file = tmp_path / 'hold'
    hold_file.touch()

    def remove_on_third_sleep(now: _Clock) -> None:
        if now.sleeps == 3:
            hold_file.unlink()

    clock.on_sleep = remove_on_third_sleep
    import_processes.hold_while_present(str(hold_file), limit=30.0)
    assert clock.sleeps == 3
    assert not hold_file.exists()


def test_a_file_never_removed_holds_for_the_limit(tmp_path: Path, clock: _Clock) -> None:
    """The limit ends a hold whose file stays, at the first look past it."""
    hold_file = tmp_path / 'hold'
    hold_file.touch()
    import_processes.hold_while_present(str(hold_file), limit=1.0)
    assert clock.now >= 1.0
    assert clock.now - import_processes._HOLD_POLL_SECONDS < 1.0
    assert hold_file.exists()
