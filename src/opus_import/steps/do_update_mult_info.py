"""Write the checked-in presentation of the mult fields over the stored ``mult`` rows.

A column's schema can state how its field's values are presented in two ways: a
``mult_options`` list, which pins the field's values, ids, labels and order, and a
``mult_overrides`` list, which sets the label, display, grouping or pin of values the
import discovered. This step writes both over the rows in place and re-ranks the fields it
touched, so that editing a schema and deploying the code is enough to rename a value or
reorder a list, with no re-import: the ids, which the observation rows hold, never change.

The step runs only when ``--update-mult-info`` is given; the code-only deploy gives it.
Finalization applies the overrides itself (`opus_import.steps.do_finalize_mult`), and
``--do-it-all`` does not imply this step.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opus_import import import_util, mult_fields
from opus_import.mult_fields import MULT_GROUP_TABLE, MULT_TABLE
from opus_import.steps import do_finalize_mult
from opus_import.steps.do_import_mult import ABSENT_VALUE

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def update_mult_info(ctx: ImportContext) -> None:
    """Write every pinned field's list and every override, then re-rank what changed.

    A pinned field this schema holds no rows of is left alone: no observation of this
    schema uses it. For one it does, each ``mult_options`` entry's label, pin, display
    and grouping are written over the row with that id, an entry with no row is inserted,
    and each entry's group pin is written to its group. The value of an existing row is
    never touched -- it is what the row means rather than how it is shown. Then every
    column's ``mult_overrides`` is applied
    (`opus_import.steps.do_finalize_mult.apply_mult_overrides`), and the values and
    groups of every field either changed are ranked again.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

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
    touched: set[int] = set()

    for name, column in mult_fields.packaged_mult_columns().items():
        if not column.pinned:
            continue
        field_id = fields[name].field_id
        in_field = f'{q("field_id")}=%s'
        stored = {int(row[0]) for row in db.read_rows(MULT_TABLE, ['id'], in_field, [field_id])}
        if not stored:
            continue
        added: list[dict[str, Any]] = []
        groups: dict[str, int | None] = {}
        for entry in column.entry['mult_options']:
            option = import_util.read_mult_option(entry)
            presentation = {
                'label': str(option.label),
                'pin': option.pin,
                'display': option.display,
                'grouping': option.grouping,
            }
            if option.id in stored:
                db.update_row(
                    MULT_TABLE,
                    presentation,
                    f'{in_field} AND {q("id")}=%s',
                    where_params=[field_id, option.id],
                )
            else:
                value = ABSENT_VALUE if option.value is None else option.value
                added.append(
                    {'field_id': field_id, 'id': option.id, 'value': value, **presentation}
                )
            if option.grouping is not None:
                groups.setdefault(option.grouping, option.group_pin)
        if added:
            db.insert_rows(MULT_TABLE, added)
        db.upsert_rows(
            MULT_GROUP_TABLE,
            'grouping',
            [
                {'field_id': field_id, 'grouping': grouping, 'group_pin': group_pin}
                for grouping, group_pin in groups.items()
            ],
        )
        touched.add(field_id)

    touched |= do_finalize_mult.apply_mult_overrides(ctx)
    do_finalize_mult.rank_mult_fields(ctx, touched)
