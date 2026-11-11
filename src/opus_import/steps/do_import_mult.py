"""Read, cache and write the ``mult`` rows holding the ``obs_`` columns' values.

A column whose values come from a fixed set stores the id of a ``mult`` row rather than
the value itself, and that row carries how the web application presents the value: its
label, its pin, whether it is displayed, and which group it belongs to. The column's
values form one mult field (`opus_import.mult_fields`), whose rows the import reads by
``field_id``. The import computes no order: finalization ranks every field's values
(`opus_import.steps.do_finalize_mult`).

**Registration writes the fields whose values are fixed.** A column whose schema lists
its values in ``mult_options`` is a pinned field, and `register_pinned_fields`, which the
bundle registration runs, writes its rows and groups; an import never writes them.

**A value the import has never seen is written the moment it is met**, under an id from
its field's counter, ``mult_field.last_id``, taken in a short transaction of its own
(`ImportDBSuper.increment_counter`), so several import processes writing one schema never
hand out one id twice. The row is then inserted in a second short transaction. When
another process inserted the same value first, the insert meets the field's unique key on
``(field_id, value)``, and the stored row's id is read back and used; the id taken is
left unused, a gap in the field's ids that nothing depends on. With one import process no
id is ever left unused. The counter is never lowered, so an id finalization deletes is
never handed out again.

Every field is read once per bundle into `opus_import.context.ImportContext`'s cache, so
importing an index of a hundred thousand rows does not query for the same value a hundred
thousand times. A field's cache finds a value through a dictionary keyed as the server's
collation compares the stored value, so a lookup costs the same however many values the
field holds. No value is deleted or renumbered before finalization, so a value the cache
holds is always right; a value it does not find is asked of the server before it is given
a new id, since the key is not the collation in full.

These are the mult-handling internals of `opus_import.steps.do_import`, not a step of
their own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from opus_import import import_util, mult_fields
from opus_import.importdb.super import ImportDBError
from opus_import.mult_fields import MULT_FIELD_TABLE, MULT_GROUP_TABLE, MULT_TABLE
from opus_support import collation_key

if TYPE_CHECKING:
    from opus_import.context import ImportContext

MultRow = dict[str, Any]
"""One ``mult`` row: ``id``, ``value``, ``label``, ``pin``, ``display`` and ``grouping``."""

#: The columns of ``mult`` the import reads and writes; ``field_id`` is added on writing,
#: and ``disp_rank`` is finalization's.
MULT_ROW_COLUMNS = ('id', 'value', 'label', 'pin', 'display', 'grouping')

#: The columns of a row that say how its value is presented, which are all that an
#: existing row's write ever changes: a row's id and value are what it means.
PRESENTATION_COLUMNS = ('label', 'pin', 'display', 'grouping')

#: The value a field stores for an absent value. A unique key does not deduplicate
#: NULLs, so the absent value is the empty string, never NULL.
ABSENT_VALUE = ''

#: The label of the absent value when a field has to be given one.
ABSENT_LABEL = 'N/A'

#: The largest id ``mult.id`` and the observation columns that hold it can store, a
#: ``SMALLINT UNSIGNED``.
MAX_MULT_ID = 65_535

#: The id a pinned field's absent value takes when its ``mult_options`` list has none:
#: the largest id, which no list may give (the schema check refuses it), so a value a
#: later release adds to the list can never land on it.
PINNED_ABSENT_ID = MAX_MULT_ID


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
        by_id: The rows keyed by id.
        by_value: The rows keyed by the `opus_support.collation_key` of their value, so a
            value the server would call equal to a stored one finds it; where two rows
            share a key, the first.
        groups: Each group's pin, keyed by the `collation_key` of its name.
        overridden: The `collation_key` of every value the column's ``mult_overrides``
            presents, whose stored presentation finalization sets.
    """

    name: str
    field_id: int
    pinned: bool
    rows: list[MultRow] = field(default_factory=list)
    by_id: dict[int, MultRow] = field(default_factory=dict)
    by_value: dict[str, MultRow] = field(default_factory=dict)
    groups: dict[str, int | None] = field(default_factory=dict)
    overridden: frozenset[str] = frozenset()

    def remember(self, row: MultRow) -> None:
        """Add a row read from the database or the schema, or a new one, to the cache.

        Parameters:
            row: The row, keyed by `MULT_ROW_COLUMNS`.
        """
        self.rows.append(row)
        self.by_id[row['id']] = row
        self.by_value.setdefault(collation_key(row['value']), row)

    def remember_group(self, grouping: str, group_pin: int | None) -> None:
        """Add a group read from the database or the schema to the cache.

        Parameters:
            grouping: The group's name.
            group_pin: The group's pin, or None.
        """
        self.groups.setdefault(collation_key(grouping), group_pin)

    def find(self, value: str) -> MultRow | None:
        """Return the row a value is stored under, as far as the cache knows.

        Parameters:
            value: The value, as it would be stored.

        Returns:
            The first row whose value has the same `collation_key`, or None.
        """
        return self.by_value.get(collation_key(value))


@dataclass
class OptionChanges:
    """What laying a pinned column's ``mult_options`` over its stored rows changes.

    Attributes:
        new_rows: The entries the field does not store, as rows to insert.
        updated_rows: Stored rows whose presentation the list changes, to update by id.
        group_rows: The groups added, or whose pin the list changes, as ``mult_group``
            rows.
    """

    new_rows: list[MultRow] = field(default_factory=list)
    updated_rows: list[MultRow] = field(default_factory=list)
    group_rows: list[dict[str, Any]] = field(default_factory=list)


def _stored_value(val: Any) -> str:
    """Return a value in the form a ``mult`` row stores it.

    Parameters:
        val: The value an obs class computed, or None.

    Returns:
        The value as a string; `ABSENT_VALUE` for None.
    """
    return ABSENT_VALUE if val is None else str(val)


def option_rows(column: dict[str, Any]) -> list[tuple[MultRow, int | None]]:
    """Return a pinned column's ``mult_options`` as rows, each with its group's pin.

    Parameters:
        column: The column's schema entry, which carries ``mult_options``.

    Returns:
        One row per entry, in the entry's order, beside the group pin it gives; the
        absent value, null in the schema, is the empty string.

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


def _group_row(cache: MultFieldCache, grouping: str, group_pin: int | None) -> dict[str, Any]:
    """Return the ``mult_group`` row of one group of a field."""
    return {'field_id': cache.field_id, 'grouping': grouping, 'group_pin': group_pin}


def read_mult_field(
    ctx: ImportContext, field_name: str, table_column: dict[str, Any]
) -> MultFieldCache:
    """Return a mult field's rows, reading them into the cache the first time.

    The rows are what ``mult`` holds for the field: a pinned field's, which registration
    wrote from its ``mult_options``, and every value an import has added since. A field
    with none starts out empty, and the import fills it as it meets values.

    Parameters:
        ctx: The import run's context, for the open database, the caches and the
            arguments.
        field_name: The field's qualified name.
        table_column: The definition of a column whose values are the field's.

    Returns:
        The field's cache itself, which `update_mult_table` adds a value to.

    Raises:
        KeyError: If ``mult_field`` holds no row for the field, which registration
            writes for every field the packaged schemas declare.
    """
    if field_name in ctx.mult_table_cache:
        return ctx.mult_table_cache[field_name]

    info = mult_fields.read_mult_fields(ctx)[field_name]
    cache = MultFieldCache(
        field_name,
        info.field_id,
        pinned='mult_options' in table_column,
        overridden=frozenset(
            collation_key(_stored_value(override['value']))
            for override in table_column.get('mult_overrides', [])
        ),
    )
    _read_stored_rows(ctx, cache)
    ctx.mult_table_cache[field_name] = cache
    return cache


def _read_stored_rows(ctx: ImportContext, cache: MultFieldCache) -> None:
    """Read a field's stored rows and groups into its cache.

    Parameters:
        ctx: The import run's context, for the open database and the arguments.
        cache: The field's cache, empty.
    """
    db = ctx.db
    assert db is not None
    if not ctx.args.suppress_mult_messages:
        import_util.log_debug(ctx, f'Reading mult field "{cache.name}"')
    q = db.quote_identifier
    in_field = f'{q("field_id")}=%s'
    for values in db.read_rows(
        MULT_TABLE, MULT_ROW_COLUMNS, f'{in_field} ORDER BY {q("id")}', [cache.field_id]
    ):
        cache.remember(dict(zip(MULT_ROW_COLUMNS, values, strict=True)))
    for grouping, group_pin in db.read_rows(
        MULT_GROUP_TABLE, ['grouping', 'group_pin'], in_field, [cache.field_id]
    ):
        cache.remember_group(grouping, group_pin)


def register_pinned_fields(ctx: ImportContext) -> None:
    """Write every pinned field's rows and groups from its column's ``mult_options``.

    Bundle registration (`opus_import.steps.do_register`) runs this inside its one
    transaction, after the fields are numbered, so no import writes a pinned field's rows.
    Each field's list is laid over its stored rows (`lay_options_over`): an entry the
    field lacks is inserted, a stored row whose presentation the list changes is updated
    by id, and each group is written with its pin. The field's ``last_id`` is then set to
    the highest id it holds, leaving out `PINNED_ABSENT_ID`.

    Parameters:
        ctx: The import run's context, for the open database and the log.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    fields = mult_fields.ensure_mult_fields(ctx)
    for name, column in mult_fields.packaged_mult_columns().items():
        if not column.pinned:
            continue
        cache = MultFieldCache(name, fields[name].field_id, pinned=True)
        _read_stored_rows(ctx, cache)
        changes = lay_options_over(ctx, cache, column.entry)
        if changes.new_rows:
            db.insert_rows(
                MULT_TABLE, [{'field_id': cache.field_id, **row} for row in changes.new_rows]
            )
        for row in changes.updated_rows:
            db.update_row(
                MULT_TABLE,
                {key: row[key] for key in PRESENTATION_COLUMNS},
                f'{q("field_id")}=%s AND {q("id")}=%s',
                where_params=[cache.field_id, row['id']],
            )
        db.upsert_rows(MULT_GROUP_TABLE, 'grouping', changes.group_rows)
        ids = [row['id'] for row in cache.rows if row['id'] != PINNED_ABSENT_ID]
        if ids:
            db.update_row(
                MULT_FIELD_TABLE,
                {'last_id': max(ids)},
                f'{q("field_id")}=%s',
                where_params=[cache.field_id],
            )


def lay_options_over(
    ctx: ImportContext, cache: MultFieldCache, column: dict[str, Any]
) -> OptionChanges:
    """Lay a pinned column's ``mult_options`` over the field's stored rows.

    An entry whose id the field stores with the same value gives that row its label,
    pin, display and grouping; an entry neither of whose id or value the field stores is
    a new row. An entry that disagrees with a stored row -- its id stored under another
    value, or its value stored under another id -- is an error, logged once a run, and
    the stored row stays as it is: changing it would change what every observation
    holding its id means.

    Parameters:
        ctx: The import run's context, for the log.
        cache: The field's cache, holding its stored rows; the list's rows and groups
            are added to it.
        column: The column's schema entry.

    Returns:
        The rows and groups to write.
    """
    changes = OptionChanges()
    for row, group_pin in option_rows(column):
        stored = cache.by_id.get(row['id'])
        holder = cache.find(row['value'])
        if stored is not None and collation_key(stored['value']) != collation_key(row['value']):
            import_util.log_nonrepeating_error(
                ctx,
                f'mult_options of mult field "{cache.name}" gives id {row["id"]} the value '
                f'"{row["value"]}", but the field stores "{stored["value"]}" under it; the '
                'stored row stays',
            )
            continue
        if stored is None and holder is not None:
            import_util.log_nonrepeating_error(
                ctx,
                f'mult_options of mult field "{cache.name}" gives the value "{row["value"]}" '
                f'id {row["id"]}, but the field stores it under id {holder["id"]}; the stored '
                'row stays',
            )
            continue
        if stored is None:
            cache.remember(row)
            changes.new_rows.append(row)
        elif any(stored[key] != row[key] for key in PRESENTATION_COLUMNS):
            stored.update({key: row[key] for key in PRESENTATION_COLUMNS})
            changes.updated_rows.append(stored)
        grouping = row['grouping']
        if grouping is None:
            continue
        key = collation_key(grouping)
        if key not in cache.groups or cache.groups[key] != group_pin:
            cache.groups[key] = group_pin
            changes.group_rows.append(_group_row(cache, grouping, group_pin))
    return changes


def _find_or_ask(ctx: ImportContext, cache: MultFieldCache, value: str) -> MultRow | None:
    """Return the row a value is stored under, asking the server when the cache misses.

    `opus_support.collation_key` is not the server's collation in full, so a value the
    cache does not find may still be one the server holds, which its unique key would
    refuse a second row of. The server's answer is kept in the cache under the value's
    key.

    Parameters:
        ctx: The import run's context, for the open database.
        cache: The field's cache.
        value: The value, as it would be stored.

    Returns:
        The row, or None when neither the cache nor the server holds the value.
    """
    row = cache.find(value)
    if row is not None:
        return row
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    found = db.read_rows(
        MULT_TABLE,
        MULT_ROW_COLUMNS,
        f'{q("field_id")}=%s AND {q("value")}=%s',
        [cache.field_id, value],
    )
    if not found:
        return None
    row = cache.by_id.get(found[0][0])
    if row is None:
        row = dict(zip(MULT_ROW_COLUMNS, found[0], strict=True))
        cache.remember(row)
    cache.by_value[collation_key(value)] = row
    return row


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
    row = _find_or_ask(ctx, read_mult_field(ctx, name, table_column), _stored_value(val))
    return None if row is None else int(row['id'])


def _differences(
    cache: MultFieldCache,
    existing: MultRow,
    incoming: MultRow,
    group_pin: int | None,
) -> list[str]:
    """Return how an incoming presentation of a stored value differs from the stored one.

    Parameters:
        cache: The field's cache, for its groups' pins.
        existing: The stored row.
        incoming: The presentation computed for the value, keyed as a row.
        group_pin: The pin computed for the value's group.

    Returns:
        One ``column stored -> computed`` entry per column that differs, the group's pin
        among them when the value has a group the field knows.
    """
    differences = [
        f'{key} {existing[key]!r} -> {incoming[key]!r}'
        for key in PRESENTATION_COLUMNS
        if existing[key] != incoming[key]
    ]
    grouping = incoming['grouping']
    if grouping is not None:
        key = collation_key(grouping)
        if key in cache.groups and cache.groups[key] != group_pin:
            differences.append(f'group_pin {cache.groups[key]!r} -> {group_pin!r}')
    return differences


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

    A new value takes the next id of its field's counter and is inserted at once
    (`_add_value`). Nothing here orders the values: finalization ranks them. A value the
    cache does not find is asked of the server first (`_find_or_ask`).

    A value the field already holds keeps its row. When the field is not pinned, the
    column's ``mult_overrides`` does not present the value, and the incoming label,
    display, pin, grouping or group pin differs from the stored one, the stored row stays
    and a warning, logged once a run, names the field, the value and both
    presentations, and points at ``mult_overrides`` as the way to set the stored one.

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
        which fails the bundle; the row is given the id of the field's absent value, so
        an import run with ``--ignore-errors`` carries on. A pinned field whose list has
        no absent value is given one under `PINNED_ABSENT_ID`, which finalization deletes
        once no observation holds it. In a pool worker, the
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
    cache = read_mult_field(ctx, name, table_column)
    incoming: MultRow = {
        'value': _stored_value(val),
        'label': str(label),
        'pin': pin,
        'display': disp,
        'grouping': grouping,
    }

    existing = _find_or_ask(ctx, cache, incoming['value'])
    if existing is not None:
        if not cache.pinned and collation_key(incoming['value']) not in cache.overridden:
            differences = _differences(cache, existing, incoming, group_pin)
            if differences:
                import_util.log_nonrepeating_warning(
                    ctx,
                    f'Mult field "{name}" holds value "{existing["value"]}" as '
                    f'"{existing["label"]}", and a bundle computes "{incoming["label"]}" '
                    f'({"; ".join(differences)}); the stored row stays. A mult_overrides '
                    "entry in the column's schema sets its presentation",
                )
        return existing['id']

    if cache.pinned:
        import_util.log_nonrepeating_error(
            ctx,
            f'Unable to add value "{incoming["value"]}" to preprogrammed mult field "{name}"',
        )
        absent = _find_or_ask(ctx, cache, ABSENT_VALUE)
        if absent is not None:
            return absent['id']
        incoming = {
            'value': ABSENT_VALUE,
            'label': ABSENT_LABEL,
            'pin': None,
            'display': 'Y',
            'grouping': None,
        }
        return _add_value(ctx, cache, incoming, None, PINNED_ABSENT_ID)

    return _add_value(ctx, cache, incoming, group_pin, None)


def _take_id(ctx: ImportContext, cache: MultFieldCache) -> int:
    """Take the next id of a field's counter, ``mult_field.last_id``, in its own transaction.

    Parameters:
        ctx: The import run's context, for the open database.
        cache: The field's cache.

    Returns:
        The id, one above the highest the field had handed out.
    """
    db = ctx.db
    assert db is not None
    return db.retrying(
        f'Taking an id in mult field "{cache.name}"',
        lambda: db.increment_counter(MULT_FIELD_TABLE, 'last_id', 'field_id', cache.field_id),
    )


def _add_value(
    ctx: ImportContext,
    cache: MultFieldCache,
    incoming: MultRow,
    group_pin: int | None,
    new_id: int | None,
) -> int:
    """Write a new value to its field, and its group if the field lacks it.

    The row is inserted in a transaction of its own. If another process inserted the
    same value first, the insert meets the field's unique key on ``(field_id, value)``;
    that row is read back and its id used, and the id taken here is left unused.

    Parameters:
        ctx: The import run's context, for the open database, the arguments and the log.
        cache: The field's cache; the row is added to it.
        incoming: The value and its presentation, keyed as a row without its id.
        group_pin: The group's pin, or None.
        new_id: The id to give it, or None to take the next from the field's counter
            (`_take_id`).

    Returns:
        The id the value is stored under.

    Raises:
        MultIdOverflowError: If the id would exceed `MAX_MULT_ID`.
        ImportDBError: If the insert fails for another reason, such as a value the
            server's collation calls equal to one the field holds under another key;
            the message names the field and the value.
    """
    if new_id is None:
        new_id = _take_id(ctx, cache)
    if new_id > MAX_MULT_ID:
        raise MultIdOverflowError(
            f'Mult field "{cache.name}" has no id left for value "{incoming["value"]}": '
            f'its ids are a SMALLINT UNSIGNED, whose largest is {MAX_MULT_ID}'
        )
    db = ctx.db
    assert db is not None
    row = {'id': new_id, **incoming}
    try:
        with db.failures_expected():
            db.insert_row(MULT_TABLE, {'field_id': cache.field_id, **row})
    except ImportDBError as e:
        stored = _find_or_ask(ctx, cache, row['value']) if db.is_duplicate_key_error(e) else None
        if stored is None:
            ctx.logger.log(
                'fatal',
                f'Mult field "{cache.name}": inserting the value "{row["value"]}" under id '
                f'{new_id} failed: {e}',
            )
            raise
        import_util.log_debug(
            ctx,
            f'Mult field "{cache.name}": another process stored "{stored["value"]}" first, '
            f'under id {stored["id"]}',
        )
        return int(stored['id'])
    cache.remember(row)
    grouping = row['grouping']
    if grouping is not None and collation_key(grouping) not in cache.groups:
        cache.remember_group(grouping, group_pin)
        db.insert_rows_keeping_existing(
            MULT_GROUP_TABLE, 'field_id', [_group_row(cache, grouping, group_pin)]
        )
    if not ctx.args.suppress_mult_messages:
        import_util.log_info(
            ctx,
            f'Added new value "{row["value"]}" ("{row["label"]}") to mult field "{cache.name}"',
        )
    return new_id
