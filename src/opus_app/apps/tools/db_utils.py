################################################################################
#
# tools/db_utils.py
#
################################################################################

"""Model lookup by category name, and the labels behind the mult ids.

The observation tables share a naming convention (`obs_pds` holds the rows of the
`ObsPds` model), so code that has to work across all of them looks a model class up
by table name instead of importing it. A ``param_info`` category is usually a table of its
own, but the surface geometry categories are not: each body's category,
``obs_surface_geometry__<target>``, is the rows of ``obs_surface_geometry_target`` holding
the body's id, and the selector category, ``obs_surface_geometry_name``, is the whole of
that table. `resolve_category` turns a category into the table, the alias a statement
names the table by, and the body's id, from ``table_names``. A mult field stores the id of a ``mult`` row
rather than a value, so displaying one means a second lookup, which reads the process's
copy of the field's rows from `import_constants`.

The MySQL error numbers are the failures that callers of these tables catch when
they inspect a database exception; `is_lock_timeout_error` and `is_deadlock_error` are
the places that read the numbers of a lock wait that timed out and of a broken deadlock.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.apps import apps
from django.conf import settings

from opus_app.apps.tools import sql_builder
from opus_app.apps.tools.import_constants import mult_table, table_names
from opus_support import parse_form_type

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.db.models import QuerySet

    from opus_app.apps.paraminfo.models import ParamInfo

MYSQL_TABLE_NOT_EXISTS = 1146
MYSQL_EXECUTION_TIME_EXCEEDED = 3024
MYSQL_LOCK_WAIT_TIMEOUT = 1205
MYSQL_DEADLOCK = 1213


def is_lock_timeout_error(exc: BaseException) -> bool:
    """Return whether a database exception is a lock wait that timed out.

    Parameters:
        exc: The exception, as Django raises it, which carries the driver's error
            number as its first argument.

    Returns:
        True for MySQL's error 1205.
    """
    return bool(exc.args) and exc.args[0] == MYSQL_LOCK_WAIT_TIMEOUT


def is_deadlock_error(exc: BaseException) -> bool:
    """Return whether a database exception is a deadlock the server broke.

    Parameters:
        exc: The exception, as Django raises it, which carries the driver's error
            number as its first argument.

    Returns:
        True for MySQL's error 1213.
    """
    return bool(exc.args) and exc.args[0] == MYSQL_DEADLOCK


def table_model_from_name(table_name: str) -> type[Any]:
    """Given a table name (obs_pds) return the Django model class (ObsPds).

    Parameters:
        table_name: The name of the table in the database.

    Returns:
        The model class the `search` app registers for that table. Which class it
        is depends on the table name, so it carries no static type of its own.

    Raises:
        LookupError: If the `search` app has no model for that table.
    """
    model_name = ''.join(table_name.title().split('_'))

    # This can throw LookupError
    return apps.get_model('search', model_name)


def is_ascii_column(table_name: str, column_name: str) -> bool:
    """Return whether a table's column holds ASCII, as its generated model declares.

    A column in the ASCII character set compares only with ASCII text
    (`sql_builder.ascii_comparable`).

    Parameters:
        table_name: The table, such as a `ResolvedCategory.table`.
        column_name: The column.

    Returns:
        True if the model's field names the ASCII collation.

    Raises:
        LookupError: If the `search` app has no model for the table.
        django.core.exceptions.FieldDoesNotExist: If the model has no such field.
    """
    field = table_model_from_name(table_name)._meta.get_field(column_name)
    return getattr(field, 'db_collation', None) == sql_builder.ASCII_COLLATION


#: The column of a surface geometry category's table holding the body's id.
TARGET_COLUMN = 'target_name'


@dataclass(frozen=True)
class ResolvedCategory:
    """Where a category's rows are, as a statement or the ORM reads them.

    Attributes:
        model: The model class of the table.
        table: The table holding the category's rows.
        alias: The name statements give the table, which is the category's name, so that
            every ``<category>.<column>`` reference reads the category's rows.
        target_name: The body's id in the surface geometry selector's mult field, which
            the table's ``target_name`` column holds in the category's rows, or None for a
            category holding every row of its table.
    """

    model: type[Any]
    table: str
    alias: str
    target_name: int | None

    @property
    def source(self) -> sql_builder.TableSource:
        """The table as a FROM clause or a join names it, under the alias when it differs.

        Returns:
            The table's name when the alias is the table's own name; otherwise an
            `opus_app.apps.tools.sql_builder.AliasedTable` naming the table under the
            alias.
        """
        if self.table == self.alias:
            return self.table
        return sql_builder.AliasedTable(self.table, self.alias)

    @property
    def is_selector(self) -> bool:
        """Whether the category is the selector, every row of a table under another name.

        Several of an observation's rows can be in such a category, so joining it onto
        ``obs_general`` would repeat the observation.

        Returns:
            True when the category reads a table under another name and keeps to no
            body's rows; False for a table of its own and for a body's category.
        """
        return self.table != self.alias and self.target_name is None

    def target_condition(self) -> sql_builder.Expr | None:
        """Return the condition that limits the table's rows to the category's.

        Returns:
            ``<alias>.target_name = %s`` with the body's id, or None for a category holding
            every row of its table.
        """
        if self.target_name is None:
            return None
        return sql_builder.binary_op(
            sql_builder.column(TARGET_COLUMN, self.alias), '=', sql_builder.value(self.target_name)
        )

    def restrict(self, select: sql_builder.Select) -> None:
        """Keep a statement reading the category to the category's rows.

        Parameters:
            select: A statement whose FROM clause names `source`; `target_condition` is
                added to its WHERE clause, when there is one.
        """
        condition = self.target_condition()
        if condition is not None:
            select.add_where(condition)


@functools.cache
def _category_tables() -> dict[str, tuple[str, int | None]]:
    """Return the table and body id of every category that is not a table of its own.

    Returns:
        The ``table_names`` rows that name a ``physical_table``, as a mapping from the
        category to that table and the row's ``target_name``, which is None for a
        category holding every row of the table. A category that is a table of its own
        has no entry.
    """
    return {
        row.table_name: (row.physical_table, row.target_name)
        for row in table_names()
        if row.physical_table is not None
    }


def resolve_category(category: str) -> ResolvedCategory:
    """Return the table, alias, body id and model a category's rows are read through.

    Parameters:
        category: A ``param_info`` category, such as ``obs_general``,
            ``obs_surface_geometry__saturn`` or ``obs_surface_geometry_name``.

    Returns:
        For a category whose ``table_names`` row names a ``physical_table``, that table
        under the category's name with the row's ``target_name``; for any other, the
        table of the category's name with no body.

    Raises:
        LookupError: If the `search` app has no model for the table.
    """
    table, target_name = _category_tables().get(category, (category, None))
    return ResolvedCategory(table_model_from_name(table), table, category, target_name)


def query_table_for_opus_id(table_name: str, opus_id: str) -> QuerySet[Any]:
    """Return a category's rows of one observation.

    Parameters:
        table_name: The category, resolved by `resolve_category`.
        opus_id: The observation whose rows are wanted.

    Returns:
        A queryset of the category's rows for the observation, which holds at most one
        row except for the surface geometry selector category, which holds one per body.

    Raises:
        LookupError: If the `search` app has no model for the category's table.
    """
    # This can throw LookupError
    resolved = resolve_category(table_name)
    opus_id = sql_builder.ascii_comparable(opus_id)
    # obs_general holds opus_id itself; every other table reaches it through its
    # obs_general relation, so the two need different lookups.
    # The model class is chosen by name, so its manager and everything that comes
    # off it are untyped; every return is that table's queryset.
    if table_name == 'obs_general':
        return resolved.model.objects.filter(opus_id=opus_id)  # type: ignore[no-any-return]
    rows = resolved.model.objects.filter(obs_general__opus_id=opus_id)
    if resolved.target_name is not None:
        rows = rows.filter(**{TARGET_COLUMN: resolved.target_name})
    return rows  # type: ignore[no-any-return]


def observation_has_body(
    category: ResolvedCategory, opus_id: str, targets: dict[str, frozenset[int]]
) -> bool:
    """Return whether one observation has rows of a surface geometry body's category.

    Parameters:
        category: A body's category, whose `ResolvedCategory.target_name` is not None.
        opus_id: The observation.
        targets: The bodies the observation has rows of, per table, which this fills from
            `targets_for_opus_id` the first time a table is asked about, so one query
            answers for every body's category of the table.

    Returns:
        True if the observation has a row holding the category's body.

    Raises:
        LookupError: If the `search` app has no model for the category's table.
    """
    if category.table not in targets:
        targets[category.table] = targets_for_opus_id(category.table, opus_id)
    return category.target_name in targets[category.table]


def targets_for_opus_id(table: str, opus_id: str) -> frozenset[int]:
    """Return the bodies one observation has rows of in a table the bodies' categories share.

    One query answers for every body's category of the table, which
    `query_table_for_opus_id` would answer one category at a time.

    Parameters:
        table: The table, a `ResolvedCategory.table` of a body's category.
        opus_id: The observation.

    Returns:
        The ``target_name`` of each of the observation's rows.

    Raises:
        LookupError: If the `search` app has no model for the table.
    """
    rows = table_model_from_name(table).objects.filter(
        obs_general__opus_id=sql_builder.ascii_comparable(opus_id)
    )
    return frozenset(rows.values_list(TARGET_COLUMN, flat=True))


def lookup_pretty_value_for_mult(param_info: ParamInfo, value: Any, cvt_null: bool) -> str | None:
    """Given a param_info for a mult and the mult value, return the pretty label.

    Parameters:
        param_info: The field the value belongs to.
        value: What the observation's column holds, which is the id of one of the
            field's ``mult`` rows.
        cvt_null: Whether the field's absent value should be reported by its label
            rather than as nothing at all.

    Returns:
        The label to display, or None when the field is not a mult one, when the
        field has no such row, or when the row is the absent value and `cvt_null`
        is false.
    """
    if param_info.form_type is None:  # pragma: no cover - import error
        return None

    (form_type, _form_type_format, _form_type_unit_id) = parse_form_type(param_info.form_type)

    if form_type not in settings.MULT_FORM_TYPES:  # pragma: no cover - import error
        return None

    rows = mult_table(param_info.param_qualified_name()).rows
    row = rows.get(int(value)) if value is not None else None
    if row is None:  # pragma: no cover - import error
        return None
    if not cvt_null and row.is_absent:
        return None
    return row.label


def lookup_pretty_value_for_mult_list(
    param_info: ParamInfo, mult_vals: Iterable[Any], cvt_null: bool
) -> str:
    """Given a param_info for a mult list and its values, return the pretty labels.

    Parameters:
        param_info: The field the values belong to.
        mult_vals: What the observation's column holds, which is the ids of the
            field's ``mult`` rows.
        cvt_null: Whether the field's absent value should be reported by its label
            rather than as nothing at all.

    Returns:
        The labels of those rows, separated by commas.
    """
    result_list = []
    for mult_val in mult_vals:
        ret = lookup_pretty_value_for_mult(param_info, mult_val, cvt_null=cvt_null)
        result_list.append(ret)
    # lookup_pretty_value_for_mult returns None for a field's absent value when
    # cvt_null is false, and joining a None raises TypeError. That is a real fault
    # rather than a typing artifact, and choosing what a null should display as
    # belongs to the caller that passes cvt_null, so the declaration is left honest
    # and the fault is recorded instead of being cast away.
    return ','.join(result_list)  # type: ignore[arg-type]
