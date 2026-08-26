"""Importing an `opus_import.util` tool must do nothing.

Both tools used to run their whole job in the module body: `retrieve_ra_dec` issued one
live SIMBAD HTTP request per star in `STARS` -- about 160 of them -- and
`dump_pds_definitions` read ``sys.argv[1]``, so importing it with no arguments raised
`IndexError`. PR-21 points Sphinx autodoc at every module in the package, so this is the
property that keeps a documentation build off the network.

These tests import the modules in a subprocess with the network and ``sys.argv`` set up
to make any regression loud rather than slow.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

MODULES = ['opus_import.util.dump_pds_definitions', 'opus_import.util.retrieve_ra_dec']

#: Loads the tools' third-party dependencies, then makes every way of opening a
#: connection raise. The dependencies come first so that the block only ever sees a
#: connection the module under test opened itself, and so that importing `ssl` (which
#: subclasses `socket.socket`) still works. A module that reaches SIMBAD at import time
#: then fails loudly here instead of hanging or making 160 live requests.
_BLOCK_NETWORK = """
import pdsparser
import requests
import socket

def _no_network(*args, **kwargs):
    raise AssertionError('the module opened a network connection at import time')

socket.getaddrinfo = _no_network
socket.create_connection = _no_network
socket.socket.connect = _no_network
socket.socket.connect_ex = _no_network
"""


def _import_in_subprocess(module: str, argv: list[str]
                          ) -> subprocess.CompletedProcess[str]:
    """Import `module` in a fresh interpreter with `argv` and no network access."""
    script = _BLOCK_NETWORK + textwrap.dedent(f"""
        import sys
        sys.argv = {argv!r}
        import importlib
        importlib.import_module({module!r})
        print('IMPORTED')
    """)
    return subprocess.run([sys.executable, '-c', script], capture_output=True,
                          text=True, timeout=120, check=False)


@pytest.mark.parametrize('module', MODULES)
def test_importing_a_util_tool_does_nothing(module: str) -> None:
    """The module imports cleanly with no arguments and without touching the network."""
    result = _import_in_subprocess(module, argv=['prog'])

    assert result.returncode == 0, result.stderr
    assert result.stdout == 'IMPORTED\n', f'the module printed something: {result.stdout!r}'


@pytest.mark.parametrize('module', MODULES)
def test_a_util_tool_exposes_main_under_a_name_guard(module: str) -> None:
    """Each tool's work is reachable as `main` and runs only as ``__main__``."""
    import importlib

    mod = importlib.import_module(module)
    assert callable(mod.main)

    # An imported module read off the file system always has a __file__.
    assert mod.__file__ is not None
    source = Path(mod.__file__).read_text(encoding='utf-8')
    assert "if __name__ == '__main__':" in source
