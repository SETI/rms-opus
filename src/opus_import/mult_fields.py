"""The mult fields: which columns hold mult ids, and the field id each one's rows carry.

A column whose ``pi_form_type`` is a group type (`opus_import.config_data.GROUP_FORM_TYPES`)
stores the id of a row of the ``mult`` table rather than its value. Its values form one
**mult field**, named by `opus_import.import_util.mult_field_name`, and every ``mult``
row and ``mult_group`` row of the field carries the field's number, ``field_id``, from
``mult_field``.

Field ids are assigned once per schema, by `ensure_mult_fields`, over every mult field
the packaged schemas declare, in order of qualified name; a field a later release
declares takes the next id. Since ids within a field never change, neither do the values
the observation columns hold.
"""

from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from opus_import import config_data, import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext

#: The table holding every mult field's values.
MULT_TABLE = 'mult'

#: The table naming every mult field.
MULT_FIELD_TABLE = 'mult_field'

#: The table holding every mult field's groups.
MULT_GROUP_TABLE = 'mult_group'

#: The three mult tables, in the order they are created.
MULT_TABLES = (MULT_FIELD_TABLE, MULT_GROUP_TABLE, MULT_TABLE)

#: The schema files whose columns can declare mult fields.
_OBSERVATION_SCHEMAS = 'obs_*.json'


@dataclass(frozen=True)
class MultColumn:
    """A column of a packaged schema that holds mult ids.

    Attributes:
        qualified_name: The field the column's values belong to.
        table_name: The schema the column is in, which is its table's name.
        entry: The column's schema entry.
    """

    qualified_name: str
    table_name: str
    entry: dict[str, Any]

    @property
    def pinned(self) -> bool:
        """Whether the column's schema lists the field's values in ``mult_options``."""
        return 'mult_options' in self.entry


@dataclass(frozen=True)
class MultFieldInfo:
    """One ``mult_field`` row.

    Attributes:
        field_id: The field's number.
        pinned: Whether the field's values are listed in its column's ``mult_options``.
    """

    field_id: int
    pinned: bool


def is_mult_column(entry: dict[str, Any]) -> bool:
    """Return whether a schema entry is a column holding mult ids.

    Parameters:
        entry: One entry of a table schema.

    Returns:
        True for a column whose ``pi_form_type``, before any ``:`` and unit, is a group
        type, unless it is marked ``put_mults_here``.
    """
    if 'field_name' not in entry or entry.get('put_mults_here', False):
        return False
    form_type = entry.get('pi_form_type')
    if form_type is None:
        return False
    return str(form_type).split(':', 1)[0] in config_data.GROUP_FORM_TYPES


@functools.cache
def packaged_mult_columns() -> dict[str, MultColumn]:
    """Return every column of a packaged observation schema that holds mult ids.

    Returns:
        The columns, keyed by the qualified name of their field, in order of that name.
        Where two columns share a field (a ``mult_field`` key), the first schema file in
        name order supplies it.
    """
    found: dict[str, MultColumn] = {}
    for schema_file in import_util.table_schema_files(_OBSERVATION_SCHEMAS):
        table_name = schema_file.name.removesuffix('.json')
        for entry in json.loads(schema_file.read_text(encoding='utf-8')):
            if not is_mult_column(entry):
                continue
            name = import_util.mult_field_name(table_name, entry['field_name'], entry)
            found.setdefault(name, MultColumn(name, table_name, entry))
    return dict(sorted(found.items()))


def create_mult_tables(ctx: ImportContext) -> None:
    """Create ``mult_field``, ``mult_group`` and ``mult`` where the schema lacks them.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    for table_name in MULT_TABLES:
        schema = import_util.read_schema_for_table(ctx, table_name)
        # The three schema files are packaged with opus_import.
        assert schema is not None
        db.create_table(table_name, schema)


def ensure_mult_fields(ctx: ImportContext) -> dict[str, MultFieldInfo]:
    """Return every mult field's id, numbering any field ``mult_field`` lacks.

    The mult tables are created first if the schema lacks them. A field the packaged
    schemas declare and ``mult_field`` does not hold is given the next id after the
    highest there, in order of qualified name, and a field whose ``pinned`` disagrees with
    its column's schema is updated. The result is kept on the context, so only the first
    call of a run reads the table.

    Parameters:
        ctx: The import run's context, for the open database and the field cache.

    Returns:
        Each field's row keyed by its qualified name, for every field ``mult_field``
        holds, which includes every field the packaged schemas declare.
    """
    if ctx.mult_fields is not None:
        return ctx.mult_fields
    db = ctx.db
    assert db is not None
    create_mult_tables(ctx)
    q = db.quote_identifier
    fields = {
        str(name): MultFieldInfo(int(field_id), bool(pinned))
        for field_id, name, pinned in db.read_rows(
            MULT_FIELD_TABLE, ['field_id', 'qualified_name', 'pinned']
        )
    }
    next_id = max((info.field_id for info in fields.values()), default=0) + 1
    added: list[dict[str, Any]] = []
    for name, column in packaged_mult_columns().items():
        info = fields.get(name)
        if info is None:
            fields[name] = MultFieldInfo(next_id, column.pinned)
            added.append({'field_id': next_id, 'qualified_name': name, 'pinned': column.pinned})
            next_id += 1
        elif info.pinned != column.pinned:
            fields[name] = MultFieldInfo(info.field_id, column.pinned)
            db.update_row(
                MULT_FIELD_TABLE,
                {'pinned': int(column.pinned)},
                f'{q("field_id")}=%s',
                where_params=[info.field_id],
            )
    if added:
        db.insert_rows(MULT_FIELD_TABLE, [{**row, 'pinned': int(row['pinned'])} for row in added])
    ctx.mult_fields = fields
    return fields
