"""Per-process copies of the tables that change only when an import runs.

``table_names``, ``partables``, ``mult_field`` and ``mult`` hold the same rows from one
import to the next, so each worker process reads each of them once, on first use, and
answers from memory after that. Nothing here notices a new import: the deploy restarts
the workers after one, and a restarted worker starts with no copies.

Each copy is built in full before it is stored, so a thread never sees part of one.
Two threads that miss at once each build a copy, and one of the two equal copies is
kept.

A lookup by a string goes through `collation_key`, which folds case and accents the way
the server's ``utf8mb4_0900_ai_ci`` collation does, so ``saturn`` finds the row labeled
``Saturn`` here as it does in a query. The key is not the server's collation in full: it
does not ignore what the collation ignores, such as a soft hyphen or an ASCII control
character, and it maps some characters onto others the collation keeps apart (``¨``
onto a space). It agrees with the server wherever both strings are printable ASCII
(`collates_as_key`), since the collation compares those letters without regard to case
and every other printable ASCII character as itself. A lookup by a name that is not
printable ASCII, one that finds nothing under its key, and one over rows holding a string
that is not printable ASCII are therefore asked of the server, which decides them.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db.models import Q

from opus_app.apps.search.models import Mult, MultField, Partables, TableNames
from opus_support import collation_key

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


def collates_as_key(text: str) -> bool:
    """Return whether a string is one `collation_key` compares as the server does.

    A string of printable ASCII characters has a nonzero weight for every character
    under the server's collation, so two such strings are equal there exactly when their
    keys are equal. Any other string may carry a character the collation ignores, or one
    the key maps onto a character the collation keeps apart from it.

    Parameters:
        text: The string, stored or from a request.

    Returns:
        True if the string is printable ASCII.
    """
    return text.isascii() and text.isprintable()


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
def table_names_collate_as_keys() -> bool:
    """Return whether every displayed table's label and name `collates_as_key`.

    Returns:
        True when a lookup of displayed tables by `collation_key` finds every row the
        server's collation would.
    """
    return all(
        collates_as_key(row.label) and collates_as_key(row.table_name)
        for row in displayed_table_names()
    )


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


#: The value a ``mult`` row stores for an absent value.
ABSENT_MULT_VALUE = ''


@functools.cache
def _mult_field_ids() -> dict[str, int]:
    """Return every ``mult_field`` row's id, keyed by its qualified name."""
    return dict(MultField.objects.values_list('qualified_name', 'field_id'))


def mult_field_id(param_qualified_name: str) -> int:
    """Return the ``mult_field`` id of a mult field.

    Parameters:
        param_qualified_name: The field's ``<table>.<column>`` name.

    Returns:
        The id every ``mult`` row of the field carries.

    Raises:
        LookupError: If ``mult_field`` has no row of that name.
    """
    field_ids = _mult_field_ids()
    if param_qualified_name not in field_ids:
        raise LookupError(f'No mult field "{param_qualified_name}"')
    return field_ids[param_qualified_name]


@dataclass(frozen=True)
class MultRow:
    """One ``mult`` row: one value a mult field can hold.

    Attributes:
        id: What an observation's column holds for this value.
        value: The value as the importer read it, which is the empty string for the
            absent value.
        label: The value as the interface shows it.
        disp_rank: Where the value comes in the field's list, counting from 1.
    """

    id: int
    value: str
    label: str
    disp_rank: int

    @property
    def is_absent(self) -> bool:
        """Whether the row is the field's absent value."""
        return self.value == ABSENT_MULT_VALUE


@dataclass(frozen=True)
class MultTable:
    """One mult field's ``mult`` rows, held in memory.

    Attributes:
        field_id: The field's ``mult_field`` id.
        rows: The rows keyed by id.
        ids_by_key: The ids of the rows whose label or value has each `collation_key`;
            the absent value, the empty string, is not a key.
        ascii_only: Whether every label and value in the field `collates_as_key`, which
            is when `ids_by_key` finds every row the server would.
    """

    field_id: int
    rows: Mapping[int, MultRow]
    ids_by_key: Mapping[str, frozenset[int]]
    ascii_only: bool

    def ids_for(self, names: Iterable[str]) -> list[int]:
        """Return the ids of the rows a list of labels and values names.

        A row is named when its label or its value is one of the names, as the server
        compares them; the absent value, the empty string, names no row by its value.
        The names are looked up on the server instead when one of them is not printable
        ASCII or has no row under its key here, or when the field holds a name that is
        not printable ASCII; in each of those a key could disagree with the server's
        collation.

        Parameters:
            names: The labels and values, in any mix.

        Returns:
            The ids of the named rows, ascending, each once.
        """
        names = list(names)
        ids: set[int] = set()
        for name in names:
            matched = (
                self.ids_by_key.get(collation_key(name))
                if self.ascii_only and collates_as_key(name)
                else None
            )
            if matched is None:
                values = [name for name in names if name != ABSENT_MULT_VALUE]
                rows = Mult.objects.filter(field_id=self.field_id).filter(
                    Q(label__in=names) | Q(value__in=values)
                )
                return sorted(rows.values_list('id', flat=True))
            ids |= matched
        return sorted(ids)


@functools.cache
def mult_table(param_qualified_name: str) -> MultTable:
    """Return a mult field's ``mult`` rows.

    Parameters:
        param_qualified_name: The field's ``<table>.<column>`` name.

    Returns:
        The field's rows, read in full on the first call for that field.

    Raises:
        LookupError: If ``mult_field`` has no row of that name.
    """
    field_id = mult_field_id(param_qualified_name)
    rows: dict[int, MultRow] = {}
    ids_by_key: dict[str, set[int]] = {}
    ascii_only = True
    for row_id, value, label, disp_rank in Mult.objects.filter(field_id=field_id).values_list(
        'id', 'value', 'label', 'disp_rank'
    ):
        rows[row_id] = MultRow(row_id, value, label, disp_rank)
        for name in (label, value):
            if name != ABSENT_MULT_VALUE:
                ids_by_key.setdefault(collation_key(name), set()).add(row_id)
                ascii_only = ascii_only and collates_as_key(name)
    return MultTable(
        field_id,
        rows,
        {key: frozenset(ids) for key, ids in ids_by_key.items()},
        ascii_only,
    )
