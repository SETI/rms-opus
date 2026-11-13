"""The hold an importer makes at the ``hold_before_lock`` fault site."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from opus_import import import_processes


def test_no_file_holds_nothing(tmp_path: Path) -> None:
    """An absent file lets the importer go on at once."""
    started = time.monotonic()
    import_processes.hold_while_present(str(tmp_path / 'absent'), limit=5.0)
    assert time.monotonic() - started < 1.0


def test_removing_the_file_ends_the_hold(tmp_path: Path) -> None:
    """The hold lasts until the file goes, not for a fixed time."""
    hold_file = tmp_path / 'hold'
    hold_file.touch()
    remover = threading.Timer(0.5, hold_file.unlink)
    remover.start()
    started = time.monotonic()
    import_processes.hold_while_present(str(hold_file), limit=30.0)
    held = time.monotonic() - started
    remover.join()
    assert 0.4 < held < 10.0


def test_a_file_never_removed_holds_for_the_limit(tmp_path: Path) -> None:
    """The limit ends a hold whose file stays."""
    hold_file = tmp_path / 'hold'
    hold_file.touch()
    started = time.monotonic()
    import_processes.hold_while_present(str(hold_file), limit=0.3)
    assert 0.3 <= time.monotonic() - started < 5.0
    assert hold_file.exists()
