"""Per-instrument hooks for reading PDS labels that do not conform to their own rules.

Both tables are matched against a label's file name as a regular expression, and both
are empty: every label OPUS imports is currently readable as it stands. They are the
place a per-instrument workaround goes when one is not, which is why they survive with
no entries.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# These are preprocessors and callbacks for PDS label reading to handle the fact
# that so many labels are horribly broken when they are archived.

PDSTABLE_PREPROCESS: list[tuple[str, Callable[..., Any], Callable[..., Any]]] = []
"""File-name pattern, label-text preprocessor, and table callback, per instrument."""

PDSTABLE_REPLACEMENTS: list[tuple[str, dict[str, Any]]] = []
"""File-name pattern and the value replacements to hand ``pdstable``, per instrument."""
