"""Per-instrument hooks for reading PDS labels that do not conform to their own rules.

Both tables are keyed by a regular expression matched against a label's file name, and
both are empty: every label OPUS imports is readable as it stands. They are the place a
per-instrument workaround goes when one is not, which is why they survive with no
entries. Only `PDSTABLE_REPLACEMENTS` is consulted;
`opus_import.import_util.safe_pdstable_read_pds3` keeps the loop over
`PDSTABLE_PREPROCESS` commented out, so an entry added there has to be switched on as
well as written.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

PDSTABLE_PREPROCESS: list[tuple[str, Callable[..., Any], Callable[..., Any]]] = []
"""File-name pattern, label-text preprocessor, and table callback, per instrument."""

PDSTABLE_REPLACEMENTS: list[tuple[str, dict[str, Any]]] = []
"""File-name pattern and the value replacements to hand ``pdstable``, per instrument."""
