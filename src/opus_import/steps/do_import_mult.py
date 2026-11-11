"""Read, cache and write the ``mult`` rows holding the ``obs_`` columns' values.

A column whose values come from a fixed set stores the id of a ``mult`` row rather than
the value itself, and that row carries how the web application presents the value: its
label, its pin, whether it is displayed, and which group it belongs to. The column's
values form one mult field (`opus_import.mult_fields`), whose rows the import reads by
``field_id``. A value the import has never seen before is added to its field as it is
encountered, which is why the rows are written alongside the observations rather than
ahead of them. The import computes no order: finalization ranks every field's values
(`opus_import.steps.do_finalize_mult`).

Every field is read once per bundle into `opus_import.context.ImportContext`'s cache and
its new rows written at the end of the bundle, so importing an index of a hundred thousand
rows does not query for the same value a hundred thousand times. A field's cache finds a
value through a dictionary keyed as the server's collation compares the stored value, so a
lookup costs the same however many values the field holds.

These are the mult-handling internals of `opus_import.steps.do_import`, not a step of
their own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from opus_import import import_util, mult_fields
from opus_import.mult_fields import MULT_GROUP_TABLE, MULT_TABLE
from opus_support import collation_key

if TYPE_CHECKING:
    from opus_import.context import ImportContext

MultRow = dict[str, Any]
"""One ``mult`` row: ``id``, ``value``, ``label``, ``pin``, ``display`` and ``grouping``."""

#: The columns of ``mult`` the import reads and writes; ``field_id`` is added on writing,
#: and ``disp_rank`` is finalization's.
MULT_ROW_COLUMNS = ('id', 'value', 'label', 'pin', 'display', 'grouping')

#: The value a field stores for an absent value. A unique key does not deduplicate
#: NULLs, so the absent value is the empty string, never NULL.
ABSENT_VALUE = ''

#: The label of the absent value when a field has to be given one.
ABSENT_LABEL = 'N/A'

#: The largest id ``mult.id`` and the observation columns that hold it can store, a
#: ``SMALLINT UNSIGNED``.
MAX_MULT_ID = 65_535


class MultIdOverflowError(ValueError):
    """A field has run out of ids: a new value would need one above `MAX_MULT_ID`."""


@dataclass
class MultFieldCache:
    """One mult field's rows, as the import holds them while it imports a bundle.

    Attributes:
        name: The field's qualified name.
        field_id: The field's ``mult_field`` id.
        pinned: Whether the field's values are its column's ``mult_options``.
        rows: Every row, in the order it was read or added.
        by_value: The rows keyed by the `opus_support.collation_key` of their value, so a
            value the server would call equal to a stored one finds it; where two rows
            share a key, the first.
        max_id: The highest id among the rows, or -1 for a field with none.
        groups: Each group's pin, keyed by the `collation_key` of its name.
        new_rows: The rows this bundle added, which are written at its end.
        new_groups: The groups this bundle added, as ``mult_group`` rows.
        overridden: The `collation_key` of every value the column's ``mult_overrides``
            presents, whose stored presentation finalization sets.
    """

    name: str
    field_id: int
    pinned: bool
    rows: list[MultRow] = field(default_factory=list)
    by_value: dict[str, MultRow] = field(default_factory=dict)
    max_id: int = -1
    groups: dict[str, int | None] = field(default_factory=dict)
    new_rows: list[MultRow] = field(default_factory=list)
    new_groups: list[dict[str, Any]] = field(default_factory=list)
    overridden: frozenset[str] = frozenset()

    def remember(self, row: MultRow) -> None:
        """Add a row read from the database or the schema to the cache.

        Parameters:
            row: The row, keyed by `MULT_ROW_COLUMNS`.
        """
        self.rows.append(row)
        self.by_value.setdefault(collation_key(row['value']), row)
        self.max_id = max(self.max_id, row['id'])

    def remember_group(self, grouping: str, group_pin: int | None) -> None:
        """Add a group read from the database or the schema to the cache.

        Parameters:
            grouping: The group's name.
            group_pin: The group's pin, or None.
        """
        self.groups.setdefault(collation_key(grouping), group_pin)

    def find(self, value: str) -> MultRow | None:
        """Return the row a value is stored under, or None if the field has none.

        Parameters:
            value: The value, as it would be stored.

        Returns:
            The first row whose value the server's collation calls equal to it.
        """
        return self.by_value.get(collation_key(value))


def _stored_value(val: Any) -> str:
    """Return a value in the form a ``mult`` row stores it.

    Parameters:
        val: The value an obs class computed, or None.

    Returns:
        The value as a string; `ABSENT_VALUE` for None.
    """
    return ABSENT_VALUE if val is None else str(val)


def _option_rows(column: dict[str, Any]) -> list[tuple[MultRow, int | None]]:
    """Return a pinned column's ``mult_options`` as rows, each with its group's pin.

    Parameters:
        column: The column's schema entry, which carries ``mult_options``.

    Returns:
        One row per entry, in the entry's order, beside the group pin it gives.

    Raises:
        TypeError: If an entry is not the shape `opus_import.import_util.read_mult_option`
            accepts.
    """
    rows = []
    for entry in column['mult_options']:
        option = import_util.read_mult_option(entry)
        row = {
            'id': option.id,
            'value': _stored_value(option.value),
            'label': str(option.label),
            'pin': option.pin,
            'display': option.display,
            'grouping': option.grouping,
        }
        rows.append((row, option.group_pin))
    return rows


def read_or_create_mult_table(
    ctx: ImportContext, field_name: str, table_column: dict[str, Any]
) -> MultFieldCache:
    """Return a mult field's rows, reading them into the cache the first time.

    A column whose schema carries ``mult_options`` has its values fixed there, so those
    are used and the field is marked for writing. Otherwise the rows come from ``mult``,
    and a field with no rows yet starts out empty, which the import fills as it meets
    values. The first call of a run numbers the fields (`opus_import.mult_fields`).

    Parameters:
        ctx: The import run's context, for the open database, the caches and the
            arguments.
        field_name: The field's qualified name.
        table_column: The definition of a column whose values are the field's.

    Returns:
        The field's cache itself, which `update_mult_table` adds a value to.

    Raises:
        KeyError: If no packaged schema declares the field.
    """
    if field_name in ctx.mult_table_cache:
        return ctx.mult_table_cache[field_name]

    info = mult_fields.ensure_mult_fields(ctx)[field_name]
    cache = MultFieldCache(
        field_name,
        info.field_id,
        pinned='mult_options' in table_column,
        overridden=frozenset(
            collation_key(_stored_value(override['value']))
            for override in table_column.get('mult_overrides', [])
        ),
    )
    db = ctx.db
    assert db is not None

    if cache.pinned:
        if not ctx.args.suppress_mult_messages:
            import_util.log_debug(ctx, f'Using preprogrammed mult field "{field_name}"')
        for row, group_pin in _option_rows(table_column):
            cache.remember(row)
            if row['grouping'] is not None:
                cache.remember_group(row['grouping'], group_pin)
                cache.new_groups.append(_group_row(cache, row['grouping'], group_pin))
            cache.new_rows.append(row)
        ctx.modified_mult_tables.add(field_name)
    else:
        if not ctx.args.suppress_mult_messages:
            import_util.log_debug(ctx, f'Reading mult field "{field_name}"')
        q = db.quote_identifier
        in_field = f'{q("field_id")}=%s'
        for values in db.read_rows(
            MULT_TABLE, MULT_ROW_COLUMNS, f'{in_field} ORDER BY {q("id")}', [info.field_id]
        ):
            cache.remember(dict(zip(MULT_ROW_COLUMNS, values, strict=True)))
        for grouping, group_pin in db.read_rows(
            MULT_GROUP_TABLE, ['grouping', 'group_pin'], in_field, [info.field_id]
        ):
            cache.remember_group(grouping, group_pin)

    ctx.mult_table_cache[field_name] = cache
    return cache


def _group_row(cache: MultFieldCache, grouping: str, group_pin: int | None) -> dict[str, Any]:
    """Return the ``mult_group`` row of one group of a field."""
    return {'field_id': cache.field_id, 'grouping': grouping, 'group_pin': group_pin}


def mult_table_lookup_id(
    ctx: ImportContext, table_name: str, field_name: str, table_column: dict[str, Any], val: Any
) -> int | None:
    """Return the id a mult field already gives a value, without adding it.

    Parameters:
        ctx: The import run's context, for the open database and the caches.
        table_name: The observation table the column belongs to.
        field_name: The column.
        table_column: The definition of that column.
        val: The value to look up. It is compared as a string, as the server's collation
            compares the stored value; None matches the absent value.

    Returns:
        The row id, or None if the field has no row for that value.
    """
    name = import_util.mult_field_name(table_name, field_name, table_column)
    row = read_or_create_mult_table(ctx, name, table_column).find(_stored_value(val))
    return None if row is None else int(row['id'])


def update_mult_table(
    ctx: ImportContext,
    table_name: str,
    field_name: str,
    table_column: dict[str, Any],
    val: Any,
    label: Any,
    disp: str = 'Y',
    pin: int | None = None,
    grouping: str | None = None,
    group_pin: int | None = None,
) -> Any:
    """Return the id a mult field gives a value, adding a row for it if it is new.

    A new row is added to the field's cache, numbered one above the field's highest id,
    and written at the end of the bundle. Nothing here orders the values: finalization
    ranks them.

    A value the field already holds keeps its row. When the field is not pinned, the
    column's ``mult_overrides`` does not present the value, and the incoming label,
    display or grouping differs from the stored row's, the stored row stays and a
    warning, logged once a run, names the field, the value and both labels, and points at
    ``mult_overrides`` as the way to set the stored presentation.

    Parameters:
        ctx: The import run's context, for the open database, the caches and the
            arguments.
        table_name: The observation table the column belongs to.
        field_name: The column.
        table_column: The definition of that column.
        val: The value to find or add. It is stored as a string, and None as the absent
            value, the empty string.
        label: How the value is shown to users. It is rendered with ``str``.
        disp: ``'Y'`` to show the value in the search form, ``'N'`` to hide it.
        pin: The value's pin, or None.
        grouping: The group the value belongs to in the search form, or None.
        group_pin: The group's pin, or None.

    Returns:
        The row id. A value missing from a pinned field is an error, logged once a run,
        which fails the bundle; the row is given the id of the field's absent value,
        which is added if the field lacks one, so an import run with
        ``--ignore-errors`` carries on. In a pool worker, the
        `opus_import.deferred.MultRef` standing for the call, which the import's process
        makes where the serial loop would have.

    Raises:
        MultIdOverflowError: If a new value would need an id above `MAX_MULT_ID`. The
            message names the field.
    """
    if ctx.capture is not None:
        values = (val, label, disp, pin, grouping, group_pin)
        position = (ctx.current_index_row_number, ctx.current_primary_filespec)
        return ctx.capture.mult(position, table_name, field_name, values)
    name = import_util.mult_field_name(table_name, field_name, table_column)
    cache = read_or_create_mult_table(ctx, name, table_column)
    value = _stored_value(val)
    label = str(label)

    existing = cache.find(value)
    if existing is not None:
        if (not cache.pinned and collation_key(value) not in cache.overridden) and (
            existing['label'] != label
            or existing['display'] != disp
            or existing['grouping'] != grouping
        ):
            import_util.log_nonrepeating_warning(
                ctx,
                f'Mult field "{name}" holds value "{value}" as "{existing["label"]}" '
                f'(display {existing["display"]}, grouping {existing["grouping"]}); the '
                f'stored row stays, and "{label}" (display {disp}, grouping {grouping}) is '
                "ignored. A mult_overrides entry in the column's schema sets the label",
            )
        return existing['id']

    if cache.pinned:
        import_util.log_nonrepeating_error(
            ctx, f'Unable to add value "{value}" to preprogrammed mult field "{name}"'
        )
        absent = cache.find(ABSENT_VALUE)
        if absent is not None:
            return absent['id']
        return _add_value(ctx, cache, ABSENT_VALUE, ABSENT_LABEL, 'Y', None, None, None)

    return _add_value(ctx, cache, value, label, disp, pin, grouping, group_pin)


def _add_value(
    ctx: ImportContext,
    cache: MultFieldCache,
    value: str,
    label: str,
    disp: str,
    pin: int | None,
    grouping: str | None,
    group_pin: int | None,
) -> int:
    """Add a value to a field's cache, and its group if the field lacks it.

    Parameters:
        ctx: The import run's context, for the arguments and the modified fields.
        cache: The field's cache.
        value: The value as stored.
        label: Its label.
        disp: Its display.
        pin: Its pin, or None.
        grouping: Its group, or None.
        group_pin: The group's pin, or None.

    Returns:
        The new row's id.

    Raises:
        MultIdOverflowError: If the id would exceed `MAX_MULT_ID`.
    """
    next_id = cache.max_id + 1
    if next_id > MAX_MULT_ID:
        raise MultIdOverflowError(
            f'Mult field "{cache.name}" has no id left for value "{value}": its ids '
            f'are a SMALLINT UNSIGNED, whose largest is {MAX_MULT_ID}'
        )
    row = {
        'id': next_id,
        'value': value,
        'label': label,
        'pin': pin,
        'display': disp,
        'grouping': grouping,
    }
    cache.remember(row)
    cache.new_rows.append(row)
    if grouping is not None and collation_key(grouping) not in cache.groups:
        cache.remember_group(grouping, group_pin)
        cache.new_groups.append(_group_row(cache, grouping, group_pin))
    ctx.modified_mult_tables.add(cache.name)
    if not ctx.args.suppress_mult_messages:
        import_util.log_info(
            ctx, f'Added new value "{value}" ("{label}") to mult field "{cache.name}"'
        )
    return next_id


def write_mult_tables(ctx: ImportContext) -> None:
    """Write the rows and groups this bundle added to its fields out to the database.

    A pinned field's rows are written whole, and an existing row of one takes the
    schema's presentation; an unpinned field's new rows are inserted. Neither touches a
    row's ``disp_rank``, which finalization computes.

    Parameters:
        ctx: The import run's context, for the open database and the caches.
    """
    db = ctx.db
    assert db is not None
    for name in sorted(ctx.modified_mult_tables):
        cache = ctx.mult_table_cache[name]
        import_util.log_debug(ctx, f'Writing mult field "{name}"')
        rows = [{'field_id': cache.field_id, **row} for row in cache.new_rows]
        db.upsert_rows(MULT_TABLE, 'id', rows)
        db.upsert_rows(MULT_GROUP_TABLE, 'grouping', cache.new_groups)
        cache.new_rows = []
        cache.new_groups = []
