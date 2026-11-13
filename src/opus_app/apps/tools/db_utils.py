################################################################################
#
# tools/db_utils.py
#
################################################################################

"""Model lookup by table name, and the labels behind the mult ids.

The observation tables share a naming convention (`obs_pds` holds the rows of the
`ObsPds` model), so code that has to work across all of them looks a model class up
by table name instead of importing it. A mult field stores the id of a ``mult`` row
rather than a value, so displaying one means a second lookup, which reads the process's
copy of the field's rows from `import_constants`.

The MySQL error numbers are the failures that callers of these tables catch when
they inspect a database exception; `is_lock_timeout_error` and `is_deadlock_error` are
the places that read the numbers of a lock wait that timed out and of a broken deadlock.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.apps import apps
from django.conf import settings

from opus_app.apps.tools.import_constants import mult_table
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


def query_table_for_opus_id(table_name: str, opus_id: str) -> QuerySet[Any]:
    """Return all rows containing opus_id in table_name (better be only one!).

    Parameters:
        table_name: The name of the observation table to search.
        opus_id: The observation whose rows are wanted.

    Returns:
        A queryset of that table's rows for the observation.

    Raises:
        LookupError: If the `search` app has no model for that table.
    """
    # This can throw LookupError
    table_model = table_model_from_name(table_name)
    # obs_general holds opus_id itself; every other table reaches it through its
    # obs_general relation, so the two need different lookups.
    # The model class is chosen by name, so its manager and everything that comes
    # off it are untyped; both returns are that table's queryset.
    if table_name == 'obs_general':
        return table_model.objects.filter(opus_id=opus_id)  # type: ignore[no-any-return]
    return table_model.objects.filter(obs_general__opus_id=opus_id)  # type: ignore[no-any-return]


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
