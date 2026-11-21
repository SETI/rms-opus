"""Write the checked-in presentation of the mult fields over the stored ``mult`` rows.

A column's schema can state how its field's values are presented in two ways: a
``mult_options`` list, which pins the field's values, ids, labels and order, and a
``mult_overrides`` list, which sets the label, display, grouping or pin of values the
import discovered. This step writes both over the rows in place and re-ranks the fields it
touched, so that editing a schema and deploying the code is enough to rename a value or
reorder a list, with no re-import: an existing row's id and value, which the observation
rows hold and mean, never change.

The step runs only when ``--update-mult-info`` is given; the code-only deploy gives it.
Finalization applies the overrides itself (`opus_import.steps.do_finalize_mult`), and
``--do-it-all`` does not imply this step.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from opus_import import import_util, mult_fields
from opus_import.mult_fields import MULT_GROUP_TABLE, MULT_TABLE
from opus_import.steps import do_finalize_mult
from opus_import.steps.do_import_mult import PRESENTATION_COLUMNS, option_rows
from opus_support import collation_key

if TYPE_CHECKING:
    from opus_import.context import ImportContext


@dataclass
class _FieldWrites:
    """What the step writes for one pinned field.

    Attributes:
        field_id: The field.
        updates: Each stored row's id beside the presentation its entry gives it.
        inserts: The entries the field holds no row for, as ``mult`` rows.
        groups: Each group's pin, keyed by name.
    """

    field_id: int
    updates: list[tuple[int, dict[str, Any]]] = field(default_factory=list)
    inserts: list[dict[str, Any]] = field(default_factory=list)
    groups: dict[str, int | None] = field(default_factory=dict)


def update_mult_info(ctx: ImportContext) -> bool:
    """Write every pinned field's list and every override, then re-rank what changed.

    A pinned field this schema holds no rows of is left alone: no observation of this
    schema uses it. For one it does, each ``mult_options`` entry is checked against the
    stored rows first. An entry whose id the field stores with the same value writes its
    label, pin, display and grouping over that row; an entry neither of whose id or value
    the field stores is inserted, id and value with it; and an entry whose id is stored
    under another value, or whose value is stored under another id, is an error, since
    writing it would change what the observations holding the id mean. **Nothing is
    written when any entry is in error.** Each entry's group pin is written to its group.
    Then every column's ``mult_overrides`` is applied
    (`opus_import.steps.do_finalize_mult.apply_mult_overrides`), the groups left with no
    value are deleted, and the values and groups of every field either changed are
    ranked again.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        True when the step wrote what the schemas give; False when an entry disagreed
        with a stored row, each such entry having been logged as an error and nothing
        written.

    Raises:
        TypeError: If a ``mult_options`` entry is not the shape
            `opus_import.import_util.read_mult_option` accepts. That is a fault in the
            packaged schema, and stopping is better than writing a row built from values
            that landed in the wrong columns.
    """
    db = ctx.db
    assert db is not None
    q = db.quote_identifier
    fields = mult_fields.ensure_mult_fields(ctx)
    plans: list[_FieldWrites] = []
    errors: list[str] = []

    for name, column in mult_fields.packaged_mult_columns().items():
        if not column.pinned:
            continue
        field_id = fields[name].field_id
        stored = {
            int(row_id): str(value)
            for row_id, value in db.read_rows(
                MULT_TABLE, ['id', 'value'], f'{q("field_id")}=%s', [field_id]
            )
        }
        if not stored:
            continue
        held = {collation_key(value): row_id for row_id, value in stored.items()}
        writes = _FieldWrites(field_id)
        for row, group_pin in option_rows(column.entry):
            key = collation_key(row['value'])
            if row['id'] in stored and collation_key(stored[row['id']]) != key:
                errors.append(
                    f'mult_options of mult field "{name}" gives id {row["id"]} the value '
                    f'"{row["value"]}", but the field stores "{stored[row["id"]]}" under it'
                )
            elif row['id'] not in stored and key in held:
                errors.append(
                    f'mult_options of mult field "{name}" gives the value "{row["value"]}" '
                    f'id {row["id"]}, but the field stores it under id {held[key]}'
                )
            elif row['id'] in stored:
                writes.updates.append(
                    (row['id'], {part: row[part] for part in PRESENTATION_COLUMNS})
                )
            else:
                writes.inserts.append({'field_id': field_id, **row})
            if row['grouping'] is not None:
                writes.groups.setdefault(row['grouping'], group_pin)
        plans.append(writes)

    if errors:
        for message in errors:
            import_util.log_error(ctx, message)
        import_util.log_error(ctx, '--update-mult-info wrote nothing')
        return False

    for writes in plans:
        for row_id, presentation in writes.updates:
            db.update_row(
                MULT_TABLE,
                presentation,
                f'{q("field_id")}=%s AND {q("id")}=%s',
                where_params=[writes.field_id, row_id],
            )
        if writes.inserts:
            db.insert_rows(MULT_TABLE, writes.inserts)
        db.upsert_rows(
            MULT_GROUP_TABLE,
            'grouping',
            [
                {'field_id': writes.field_id, 'grouping': grouping, 'group_pin': group_pin}
                for grouping, group_pin in writes.groups.items()
            ],
        )

    touched = {writes.field_id for writes in plans}
    touched |= do_finalize_mult.apply_mult_overrides(ctx)
    do_finalize_mult.delete_empty_groups(ctx)
    do_finalize_mult.rank_mult_fields(ctx, touched)
    return True
