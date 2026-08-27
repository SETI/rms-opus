"""Make the documentation build's own extensions importable to these tests.

``docs/_ext/`` is on ``sys.path`` only while Sphinx is running, because ``conf.py``
puts it there. These tests exercise those extensions without Sphinx, so they put it
there too -- the same directory, named from this file rather than repeated as a
string.
"""

import sys
from pathlib import Path

EXT_DIR = Path(__file__).resolve().parents[2] / 'docs' / '_ext'

if str(EXT_DIR) not in sys.path:
    sys.path.insert(0, str(EXT_DIR))
