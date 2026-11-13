"""``obs_surface_geometry_target``, and the categories its rows are searched under.

Every body an observation has surface geometry for contributes one row to
``obs_surface_geometry_target``, keyed by the body's id in the selector's mult field and
the observation. The web application presents the rows as one **category** per body,
``obs_surface_geometry__<target>``, whose fields are the template's columns with the
body's name in their labels and slugs, and one more category,
``obs_surface_geometry_name``, whose one field is the selector that chooses a body.
``table_names``, ``param_info`` and ``partables`` carry a category's rows, and
``table_names`` names the table and the body each category reads.

A body's category name is a table name that does not exist. Every other constraint
category is the ``obs_`` table of its name, and the search menus, the Details page, the API
and the three tables above all work one table per category; naming each body's rows as a
table keeps that convention, so only the database layer resolves the name to
``obs_surface_geometry_target`` and the body's rows.

The bodies are the values the table holds (`stored_targets`), so a category exists
exactly when an observation has geometry for its body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from opus_import import import_util
from opus_import.mult_fields import MULT_FIELD_TABLE, MULT_TABLE

if TYPE_CHECKING:
    from collections.abc import Sequence

    from opus_import.context import ImportContext
    from opus_import.import_util import TableSchema

#: The table holding every body's surface geometry rows.
SURFACE_GEOMETRY_TABLE = 'obs_surface_geometry_target'

#: The category whose one field selects a body.
SELECTOR_CATEGORY = 'obs_surface_geometry_name'

#: The column of `SURFACE_GEOMETRY_TABLE` holding the body's id.
TARGET_COLUMN = 'target_name'

#: The mult field the body ids belong to, the selector's.
TARGET_FIELD = f'{SELECTOR_CATEGORY}.{TARGET_COLUMN}'

#: What every body's category name starts with; the encoded body name follows.
TARGET_CATEGORY_PREFIX = 'obs_surface_geometry__'


class StoredTarget(NamedTuple):
    """One body ``obs_surface_geometry_target`` holds rows of.

    Attributes:
        target_id: The body's id in the selector's mult field, which the table's
            ``target_name`` column holds.
        encoded_name: The body's name as `opus_import.import_util.encode_target_name`
            spells it, which ends its category's name.
    """

    target_id: int
    encoded_name: str


def is_target_category(name: str) -> bool:
    """Return whether a name is a body's surface geometry category.

    Parameters:
        name: A table or category name.

    Returns:
        True for a name starting with `TARGET_CATEGORY_PREFIX`.
    """
    return name.startswith(TARGET_CATEGORY_PREFIX)


def target_category(encoded_name: str) -> str:
    """Return the category of one body.

    Parameters:
        encoded_name: The body's name as `opus_import.import_util.encode_target_name`
            spells it.

    Returns:
        ``obs_surface_geometry__<encoded_name>``.
    """
    return TARGET_CATEGORY_PREFIX + encoded_name


def physical_table(name: str) -> str:
    """Return the table a table or category's rows are written to.

    Parameters:
        name: A table, or a surface geometry category.

    Returns:
        `SURFACE_GEOMETRY_TABLE` for a body's category or the selector category; the
        name itself otherwise.
    """
    if is_target_category(name) or name == SELECTOR_CATEGORY:
        return SURFACE_GEOMETRY_TABLE
    return name


def category_columns(schema: TableSchema, category: str) -> TableSchema:
    """Return the entries of a schema that describe one category's fields.

    Parameters:
        schema: The schema of the category's table, with a body's placeholders filled
            in for a body's category.
        category: The category.

    Returns:
        The entries whose ``pi_category_name`` is the category, in schema order. In a
        surface geometry schema that is the template's columns for a body's category
        and the ``target_name`` column for the selector category.
    """
    return [entry for entry in schema if entry.get('pi_category_name') == category]


def category_names(table_names: Sequence[str], targets: Sequence[StoredTarget]) -> list[str]:
    """Return the categories a set of tables and bodies present, sorted by name.

    Parameters:
        table_names: The ``obs_`` tables, `SURFACE_GEOMETRY_TABLE` among them if it
            exists.
        targets: The bodies ``obs_surface_geometry_target`` holds.

    Returns:
        Every table but `SURFACE_GEOMETRY_TABLE`, which presents instead the selector
        category and one category per body, all sorted by name.
    """
    names = [name for name in table_names if name != SURFACE_GEOMETRY_TABLE]
    if SURFACE_GEOMETRY_TABLE in table_names:
        names.append(SELECTOR_CATEGORY)
        names += [target_category(target.encoded_name) for target in targets]
    return sorted(names)


def read_category_schema(ctx: ImportContext, category: str) -> TableSchema | None:
    """Read the schema that describes one category's fields.

    Parameters:
        ctx: The import run's context, for the logger.
        category: A table, a body's category or the selector category.

    Returns:
        The table's own schema; the template with the body's placeholders filled in for
        a body's category; the template as it is packaged for the selector category; or
        None when no packaged schema describes the name.
    """
    if category == SELECTOR_CATEGORY:
        return import_util.read_schema_for_table(ctx, SURFACE_GEOMETRY_TABLE)
    return import_util.read_schema_for_table(ctx, category)


def stored_targets(ctx: ImportContext) -> list[StoredTarget]:
    """Return the bodies ``obs_surface_geometry_target`` holds rows of.

    Parameters:
        ctx: The import run's context, for the open database.

    Returns:
        One entry per distinct ``target_name`` in `SURFACE_GEOMETRY_TABLE`, its name read
        from the selector field's ``mult`` row, sorted by encoded name; none when the
        table does not exist.
    """
    db = ctx.db
    assert db is not None
    if not db.table_exists(SURFACE_GEOMETRY_TABLE):
        return []
    q = db.quote_identifier
    s, m, f, target = q('s'), q('m'), q('f'), q(TARGET_COLUMN)
    # Every interpolation is an identifier produced by quote_identifier; the one value is
    # a parameter.
    sql = (
        f'DISTINCT {s}.{target}, {m}.{q("value")} FROM {q(SURFACE_GEOMETRY_TABLE)} {s} '
        f'JOIN {q(MULT_TABLE)} {m} ON {m}.{q("id")}={s}.{target} '
        f'JOIN {q(MULT_FIELD_TABLE)} {f} ON {f}.{q("field_id")}={m}.{q("field_id")} '
        f'WHERE {f}.{q("qualified_name")}=%s'
    )
    rows = db.general_select(sql, [TARGET_FIELD])
    targets = [
        StoredTarget(int(target_id), import_util.encode_target_name(str(value)))
        for target_id, value in rows
    ]
    return sorted(targets, key=lambda target: target.encoded_name)
