"""Per-process copies of the tables that change only when an import runs.

``table_names``, ``partables`` and the ``mult_`` tables hold the same rows from one
import to the next, so each worker process reads each of them once, on first use, and
answers from memory after that. Nothing here notices a new import: the deploy restarts
the workers after one, and a restarted worker starts with no copies.

Each copy is built in full before it is stored, so a thread never sees part of one.
Two threads that miss at once each build a copy, and one of the two equal copies is
kept.

A lookup by a string goes through `collation_key`, which folds case and accents the way
the server's ``utf8mb4_0900_ai_ci`` collation does, so ``saturn`` finds the row labeled
``Saturn`` here as it does in a query. The key is not the server's collation in full: it
does not ignore what the collation ignores, such as a soft hyphen. It agrees with the
server wherever the stored string is ASCII, since the collation compares ASCII letters
without regard to case and every other ASCII character as itself. A lookup that finds
nothing under its key, or that searches a mult table holding a name that is not ASCII,
is therefore asked of the server, which decides it.
"""

from __future__ import annotations

import functools
import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.apps import apps
from django.db.models import Q

from opus_app.apps.search.models import Partables, TableNames
from opus_app.apps.tools.app_utils import get_mult_name

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


def collation_key(text: str) -> str:
    """Return the form of a string that the server's collation compares.

    The server compares strings with ``utf8mb4_0900_ai_ci``, which ignores case and
    accents, so two strings it calls equal have the same key here.

    Parameters:
        text: The string to compare.

    Returns:
        The string with its accents removed and its case folded.
    """
    decomposed = unicodedata.normalize('NFKD', text)
    return ''.join(char for char in decomposed if not unicodedata.combining(char)).casefold()


@functools.cache
def table_names() -> tuple[TableNames, ...]:
    """Return every ``table_names`` row, in display order.

    The rows are shared by every caller in the process, so a caller that sets an
    attribute on one copies it first.

    Returns:
        The rows, sorted by ``disp_order``.
    """
    return tuple(TableNames.objects.order_by('disp_order'))


@functools.cache
def displayed_table_names() -> tuple[TableNames, ...]:
    """Return the ``table_names`` rows the interface shows, in display order.

    Returns:
        The rows whose ``display`` is ``Y``, compared as the server compares it.
    """
    return tuple(row for row in table_names() if collation_key(row.display) == 'y')


@functools.cache
def _table_names_by_name() -> dict[str, TableNames]:
    """Return the ``table_names`` rows keyed by the `collation_key` of their table."""
    return {collation_key(row.table_name): row for row in table_names()}


def get_table_name(table_name: str) -> TableNames:
    """Return the ``table_names`` row describing one table.

    Parameters:
        table_name: The name of the table, such as ``obs_general``.

    Returns:
        The row, shared by every caller in the process.

    Raises:
        django.core.exceptions.ObjectDoesNotExist: If no row describes that table; it is
            the model's own ``DoesNotExist``.
    """
    try:
        return _table_names_by_name()[collation_key(table_name)]
    except KeyError:
        raise TableNames.DoesNotExist(f'No table_names row for "{table_name}"') from None


@functools.cache
def partables() -> tuple[Partables, ...]:
    """Return every ``partables`` row.

    Returns:
        The rows, which say which tables an observation's values bring into the
        results and the metadata.
    """
    return tuple(Partables.objects.all())


@dataclass(frozen=True)
class MultRow:
    """One row of a ``mult_`` table: one value a mult field can hold.

    Attributes:
        id: What an observation's column holds for this value.
        value: The value as the importer read it, which is None for the null row.
        label: The value as the interface shows it.
        disp_order: Where the value comes in the field's list.
    """

    id: int
    value: str | None
    label: str
    disp_order: str


@dataclass(frozen=True)
class MultTable:
    """A ``mult_`` table, held in memory.

    Attributes:
        model_name: The name of the table's model in the ``search`` app.
        rows: The rows keyed by id.
        ids_by_key: The ids of the rows whose label or value has each `collation_key`.
        ascii_only: Whether every label and value in the table is ASCII, which is when
            `ids_by_key` finds every row the server would.
    """

    model_name: str
    rows: Mapping[int, MultRow]
    ids_by_key: Mapping[str, frozenset[int]]
    ascii_only: bool

    def ids_for(self, names: Iterable[str]) -> list[int]:
        """Return the ids of the rows a list of labels and values names.

        A row is named when its label or its value is one of the names, as the server
        compares them; that is what the query this replaces asked for. The names are
        looked up on the server instead when one of them has no row under its key here,
        or when the table holds a name that is not ASCII, where a key could miss a row
        the server's collation matches.

        Parameters:
            names: The labels and values, in any mix.

        Returns:
            The ids of the named rows, ascending, each once.
        """
        names = list(names)
        ids: set[int] = set()
        for name in names:
            matched = self.ids_by_key.get(collation_key(name)) if self.ascii_only else None
            if matched is None:
                model = apps.get_model('search', self.model_name)
                rows = model.objects.filter(Q(label__in=names) | Q(value__in=names))
                return sorted(rows.values_list('pk', flat=True))
            ids |= matched
        return sorted(ids)


@functools.cache
def mult_table(param_qualified_name: str) -> MultTable:
    """Return the ``mult_`` table that holds a mult field's values.

    Parameters:
        param_qualified_name: The field's ``<table>.<column>`` name.

    Returns:
        The table, read in full on the first call for that field.
    """
    model_name = get_mult_name(param_qualified_name).title().replace('_', '')
    model = apps.get_model('search', model_name)
    rows: dict[int, MultRow] = {}
    ids_by_key: dict[str, set[int]] = {}
    ascii_only = True
    for row_id, value, label, disp_order in model.objects.values_list(
        'id', 'value', 'label', 'disp_order'
    ):
        rows[row_id] = MultRow(row_id, value, label, disp_order)
        for name in (label, value):
            if name is not None:
                ids_by_key.setdefault(collation_key(name), set()).add(row_id)
                ascii_only = ascii_only and name.isascii()
    return MultTable(
        model_name,
        rows,
        {key: frozenset(ids) for key, ids in ids_by_key.items()},
        ascii_only,
    )
