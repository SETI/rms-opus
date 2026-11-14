"""Finalize the mult fields: drop the values no observation holds, rename, and rank.

``--finalize`` runs `finalize_mult` after the duplicate step and before the auxiliary
tables, which read the ``mult`` rows; an append invalidates it, since a bundle replaced
or added can stop or start referencing any value. It has three parts:

1. In every field whose column does not list its values (``mult_field.pinned`` is 0), the
   ``mult`` rows whose id no observation holds are deleted. The ids in use are read one
   scan per observation table, through an unbuffered cursor, with each column's
   distinct ids collected here, so a table whose mult columns carry no key is read once
   rather than once a column. A ``mult_list`` column's ids are read from its junction
   table (`opus_import.list_junctions`), whose primary key leads with the id, so the
   distinct ids are read from the key without a scan of the observation table. A pinned field keeps every row its list gives, since the list is
   the intended set of choices; the one row it may hold beyond them, the absent value
   the import adds under `opus_import.steps.do_import_mult.PINNED_ABSENT_ID`, is deleted
   like any other once no observation holds it. A deleted id is free again: the next
   value the import adds to the field takes the field's highest id plus one, which can
   be an id deleted here.
2. Each column's ``mult_overrides`` are applied over the stored rows
   (`apply_mult_overrides`), so an override wins over a stored or computed label, and
   then every group left with no value is deleted.
3. Every field's values and groups are ranked (`rank_mult_fields`), as
   `opus_import.mult_rank` describes.

``--update-mult-info`` (`opus_import.steps.do_update_mult_info`) applies the overrides,
deletes the groups left empty and ranks the fields it touched with the same functions.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

import opus_support
from opus_import import import_util, list_junctions, mult_fields
from opus_import.mult_fields import MULT_GROUP_TABLE, MULT_TABLE
from opus_import.mult_rank import RankedGroup, RankedValue, group_ranks, value_ranks
from opus_import.steps.do_import_mult import ABSENT_VALUE, option_rows

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable

    from opus_import.context import ImportContext

#: The members a ``mult_overrides`` entry may carry besides ``value``, each a column of
#: ``mult`` it sets.
OVERRIDE_MEMBERS = ('label', 'display', 'grouping', 'pin')

#: The ids one ``DELETE`` names at most.
_DELETE_CHUNK = 1000

#: The columns of ``mult`` a rank is computed from and written back with.
_RANK_COLUMNS = ('field_id', 'id', 'value', 'label', 'pin', 'disp_rank', 'display', 'grouping')


def finalize_mult(ctx: ImportContext) -> bool:
    """Run the mult step of ``--finalize``: prune, override, then rank every field.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True; every part reports what it changed and nothing here fails the step.
    """
    fields = mult_fields.ensure_mult_fields(ctx)
    columns = mult_fields.packaged_mult_columns()
    used = referenced_mult_ids(ctx)
    for name, info in sorted(fields.items()):
        kept = used.get(name, set())
        if info.pinned and name in columns:
            kept = kept | {row['id'] for row, _pin in option_rows(columns[name].entry)}
        _delete_unreferenced(ctx, name, info.field_id, kept)
    apply_mult_overrides(ctx)
    delete_empty_groups(ctx)
    rank_mult_fields(ctx)
    return True


def referenced_mult_ids(ctx: ImportContext) -> dict[str, set[int]]:
    """Return the ids each mult field's columns hold, one scan of each observation table.

    A ``mult_list`` column's ids are read from its junction table instead, by its primary
    key, and its table is scanned only for its other mult columns.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        The ids in use, keyed by the qualified name of the field; a field no table
        references is absent.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    used: dict[str, set[int]] = defaultdict(set)
    for table_name in sorted(db.table_names(prefix='obs_')):
        schema = import_util.read_schema_for_existing_table(ctx, table_name)
        if schema is None:
            continue
        columns = [entry for entry in schema if mult_fields.is_mult_column(entry)]
        lists = set(list_junctions.list_columns(columns))
        for entry in columns:
            if entry['field_name'] not in lists:
                continue
            name = import_util.mult_field_name(table_name, entry['field_name'], entry)
            junction = q(list_junctions.junction_table(table_name, entry['field_name']))
            mult_id = q(list_junctions.JUNCTION_MULT_COLUMN)
            rows = db.general_select(f'DISTINCT {mult_id} FROM {junction}')  # nosec B608
            used[name] |= {int(row[0]) for row in rows}
        columns = [entry for entry in columns if entry['field_name'] not in lists]
        if not columns:
            continue
        names = [
            import_util.mult_field_name(table_name, entry['field_name'], entry) for entry in columns
        ]
        found: list[set[int]] = [set() for _ in columns]
        selected = ','.join(q(entry['field_name']) for entry in columns)
        for row in db.stream_select(f'{selected} FROM {q(table_name)}'):  # nosec B608
            for index, stored in enumerate(row):
                if stored is not None:
                    found[index].add(int(stored))
        for name, ids in zip(names, found, strict=True):
            used[name] |= ids
    return dict(used)


def _delete_unreferenced(ctx: ImportContext, name: str, field_id: int, used: set[int]) -> None:
    """Delete a field's ``mult`` rows whose id is not kept.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        name: The field's qualified name, for the log.
        field_id: The field.
        used: The ids kept: those the observation tables hold, and for a pinned field
            those its list gives.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    stored = {
        int(row[0]) for row in db.read_rows(MULT_TABLE, ['id'], f'{q("field_id")}=%s', [field_id])
    }
    unused = sorted(stored - used)
    if not unused:
        return
    import_util.log_info(
        ctx, f'Deleting {len(unused)} value(s) no observation holds from mult field "{name}"'
    )
    for start in range(0, len(unused), _DELETE_CHUNK):
        chunk = unused[start : start + _DELETE_CHUNK]
        placeholders = ','.join(['%s'] * len(chunk))
        db.delete_rows(
            MULT_TABLE,
            f'{q("field_id")}=%s AND {q("id")} IN ({placeholders})',
            [field_id, *chunk],
        )


def delete_empty_groups(ctx: ImportContext) -> None:
    """Delete every ``mult_group`` row no ``mult`` row of its field names.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    group, value = q(MULT_GROUP_TABLE), q(MULT_TABLE)
    db.delete_rows(
        MULT_GROUP_TABLE,
        f'NOT EXISTS (SELECT 1 FROM {value} WHERE {value}.{q("field_id")}='  # nosec B608
        f'{group}.{q("field_id")} AND {value}.{q("grouping")}={group}.{q("grouping")})',
    )


def apply_mult_overrides(ctx: ImportContext) -> set[int]:
    """Apply every column's ``mult_overrides`` to its field's stored rows.

    An override is an object with a ``value``, which names the row, and any of
    `OVERRIDE_MEMBERS`, each of which sets that column of the row; a ``grouping`` the
    field has no group for gains a ``mult_group`` row with no pin. An override naming a
    value the field does not hold is reported and skipped.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        The ids of the fields an override changed.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    fields = mult_fields.ensure_mult_fields(ctx)
    touched: set[int] = set()
    for name, column in mult_fields.packaged_mult_columns().items():
        overrides = column.entry.get('mult_overrides')
        if not overrides:
            continue
        field_id = fields[name].field_id
        for override in overrides:
            value = ABSENT_VALUE if override['value'] is None else str(override['value'])
            in_row = f'{q("field_id")}=%s AND {q("value")}=%s'
            if not db.read_rows(MULT_TABLE, ['id'], in_row, [field_id, value]):
                import_util.log_warning(
                    ctx,
                    f'mult_overrides of mult field "{name}" names value "{value}", which '
                    'the field does not hold; skipped',
                )
                continue
            assigned = {key: override[key] for key in OVERRIDE_MEMBERS if key in override}
            if not assigned:
                continue
            db.update_row(MULT_TABLE, assigned, in_row, [field_id, value])
            if assigned.get('grouping') is not None:
                _ensure_group(ctx, field_id, assigned['grouping'])
            touched.add(field_id)
    return touched


def _ensure_group(ctx: ImportContext, field_id: int, grouping: str) -> None:
    """Add a ``mult_group`` row with no pin for a group its field lacks.

    Parameters:
        ctx: The import run's context, for the open database.
        field_id: The field.
        grouping: The group's name.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    where = f'{q("field_id")}=%s AND {q("grouping")}=%s'
    if not db.read_rows(MULT_GROUP_TABLE, ['grouping'], where, [field_id, grouping]):
        db.insert_rows(
            MULT_GROUP_TABLE, [{'field_id': field_id, 'grouping': grouping, 'group_pin': None}]
        )


def _parse_functions(ctx: ImportContext) -> dict[int, Callable[[str], Any] | None]:
    """Return each field's unit parser, keyed by field id.

    Parameters:
        ctx: The import run's context, for the field ids.

    Returns:
        The parser of the unit the field's column declares
        (`opus_support.get_single_parse_function`), or None for a column with no such
        unit and for a field no packaged schema declares.
    """
    columns = mult_fields.packaged_mult_columns()
    parsers: dict[int, Callable[[str], Any] | None] = {}
    for name, info in mult_fields.ensure_mult_fields(ctx).items():
        parse = None
        if name in columns:
            _, _, unit_id = opus_support.parse_form_type(columns[name].entry['pi_form_type'])
            parse = opus_support.get_single_parse_function(unit_id)
        parsers[info.field_id] = parse
    return parsers


def _in_fields(
    ctx: ImportContext, field_ids: Collection[int] | None
) -> tuple[str | None, list[Any]]:
    """Return a WHERE clause selecting the rows of some fields, or every row.

    Parameters:
        ctx: The import run's context, for the open database.
        field_ids: The fields, or None for every field.

    Returns:
        The clause, None for every row, and its parameters.
    """
    if field_ids is None:
        return None, []
    db = ctx.db
    assert db is not None
    placeholders = ','.join(['%s'] * len(field_ids))
    return f'{db.quote_identifier("field_id")} IN ({placeholders})', sorted(field_ids)


def rank_mult_fields(ctx: ImportContext, field_ids: Collection[int] | None = None) -> None:
    """Recompute ``disp_rank`` and ``group_rank`` for every field, or for some.

    Only the rows whose rank changes are written, each by its key and only its rank.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        field_ids: The fields to rank, or None for every field.
    """
    if field_ids is not None and not field_ids:
        return
    db = ctx.db
    assert db is not None
    where, params = _in_fields(ctx, field_ids)
    parsers = _parse_functions(ctx)

    by_field: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for values in db.read_rows(MULT_TABLE, _RANK_COLUMNS, where, params):
        row = dict(zip(_RANK_COLUMNS, values, strict=True))
        by_field[int(row['field_id'])].append(row)
    q = db.quote_identifier
    for field_id, rows in sorted(by_field.items()):
        ranks = value_ranks(_ranked_values(rows), parsers.get(field_id))
        for row in _with_new_ranks(rows, 'id', 'disp_rank', ranks):
            db.update_row(
                MULT_TABLE,
                {'disp_rank': row['disp_rank']},
                f'{q("field_id")}=%s AND {q("id")}=%s',
                where_params=[field_id, row['id']],
            )

    group_columns = ('field_id', 'grouping', 'group_pin', 'group_rank')
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for values in db.read_rows(MULT_GROUP_TABLE, group_columns, where, params):
        row = dict(zip(group_columns, values, strict=True))
        groups[int(row['field_id'])].append(row)
    for field_id, rows in sorted(groups.items()):
        ranked = group_ranks([RankedGroup(row['grouping'], row['group_pin']) for row in rows])
        for row in _with_new_ranks(rows, 'grouping', 'group_rank', ranked):
            db.update_row(
                MULT_GROUP_TABLE,
                {'group_rank': row['group_rank']},
                f'{q("field_id")}=%s AND {q("grouping")}=%s',
                where_params=[field_id, row['grouping']],
            )
    import_util.log_info(ctx, f'Ranked the values and groups of {len(by_field)} mult field(s)')


def _ranked_values(rows: Iterable[dict[str, Any]]) -> list[RankedValue]:
    """Return what the ranks of some ``mult`` rows are computed from."""
    return [
        RankedValue(int(row['id']), str(row['value']), str(row['label']), row['pin'])
        for row in rows
    ]


def _with_new_ranks(
    rows: Iterable[dict[str, Any]], key: str, rank_column: str, ranks: dict[Any, int]
) -> list[dict[str, Any]]:
    """Return the rows whose stored rank differs from the one computed, with the new rank.

    Parameters:
        rows: The rows as read.
        key: The column the ranks are keyed by.
        rank_column: The column holding the rank.
        ranks: The computed ranks.

    Returns:
        A copy of each row whose rank changes, carrying the new rank.
    """
    return [
        {**row, rank_column: ranks[row[key]]} for row in rows if row[rank_column] != ranks[row[key]]
    ]
