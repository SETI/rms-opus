"""How `communicate_all` waits for processes that run at once.

Two small Python processes stand for importers: one waits on something the other does
only after writing more to its standard output than a pipe holds.
"""

import subprocess  # nosec B404 - the test runs this interpreter on its own scripts
import sys
from pathlib import Path

from import_tests.tools import build_run

#: How long the waiting process looks for the other's signal before it gives up.
_WAIT_S = 10

#: More than any operating system's pipe buffer holds.
_FLOOD_BYTES = 4 * 1024 * 1024

#: Waits for the file its first argument names, exiting 3 after its second's seconds.
_WAITER = """
import pathlib, sys, time
signal = pathlib.Path(sys.argv[1])
deadline = time.monotonic() + float(sys.argv[2])
while not signal.exists():
    if time.monotonic() > deadline:
        sys.exit(3)
    time.sleep(0.05)
print('saw it')
"""

#: Writes its second argument's count of bytes to standard output, then the file its
#: first argument names.
_FLOODER = """
import pathlib, sys
sys.stdout.write('x' * int(sys.argv[2]))
sys.stdout.flush()
pathlib.Path(sys.argv[1]).touch()
"""


def _python(script: str, *arguments: str) -> subprocess.Popen[str]:
    """Start this interpreter on a script, its output piped as text."""
    return subprocess.Popen(  # nosec B603 - this interpreter and the test's own script
        [sys.executable, '-c', script, *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_a_later_process_that_fills_its_pipe_does_not_stall_an_earlier_one(
    tmp_path: Path,
) -> None:
    """Every pipe is drained at once, so the second process gets past its flood and the
    first sees its signal, where draining the first alone would leave both waiting."""
    signal = tmp_path / 'flooded'
    waiter = _python(_WAITER, str(signal), str(_WAIT_S))
    flooder = _python(_FLOODER, str(signal), str(_FLOOD_BYTES))

    outputs = build_run.communicate_all([waiter, flooder])

    assert waiter.returncode == 0
    assert outputs[0] == ('saw it\n', '')
    assert len(outputs[1][0]) == _FLOOD_BYTES


def test_no_process_is_nothing_to_wait_for() -> None:
    """An empty list returns at once, with no thread started."""
    assert build_run.communicate_all([]) == []
