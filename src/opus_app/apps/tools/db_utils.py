################################################################################
#
# tools/db_utils.py
#
################################################################################

"""Model lookup by table name, and the labels behind the mult tables.

The observation tables share a naming convention (`obs_pds` holds the rows of the
`ObsPds` model), so code that has to work across all of them looks a model class up
by table name instead of importing it. A mult field stores the id of a row in its
own small table rather than a value, so displaying one means a second lookup; the
labels those lookups produce are cached here for the life of the process.

The MySQL error numbers are the failures that callers of these tables catch when
they inspect a database exception.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.apps import apps
from django.conf import settings

from opus_app.apps.tools.app_utils import get_mult_name
from opus_support import parse_form_type

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.db.models import QuerySet

    from opus_app.apps.paraminfo.models import ParamInfo

MYSQL_TABLE_NOT_EXISTS = 1146
MYSQL_TABLE_ALREADY_EXISTS = 1050
MYSQL_EXECUTION_TIME_EXCEEDED = 3024

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
    # opus_id is the primary key for obs_general, but a foreign key for all
    # other tables. Due to Django's design, we have to handle these cases
    # separately.
    # The model class is chosen by name, so its manager and everything that comes
    # off it are untyped; both returns are that table's queryset.
    if table_name == 'obs_general':
        return table_model.objects.filter(opus_id=opus_id) # type: ignore[no-any-return]
    return table_model.objects.filter(obs_general__opus_id=opus_id) # type: ignore[no-any-return]


# Looking up entries in the mult tables is slow, so cache them in memory as they
# are retrieved. There aren't that many mult tables or values, so this won't take
# much memory even in the worst case.
_PRETTY_MULT_CACHE: dict[tuple[str, Any], dict[str, str | None]] = {}

def lookup_pretty_value_for_mult(param_info: ParamInfo, value: Any,
                                 cvt_null: bool) -> str | None:
    """Given a param_info for a mult and the mult value, return the pretty label.

    Parameters:
        param_info: The field the value belongs to.
        value: What the observation's column holds, which is the id of a row in the
            field's mult table.
        cvt_null: Whether the mult table's null row should be reported by its label
            rather than as nothing at all.

    Returns:
        The label to display, or None when the field is not a mult one, when the
        mult table has no such row, or when the row is the null one and `cvt_null`
        is false.
    """
    if param_info.form_type is None: # pragma: no cover - import error
        return None

    (form_type, _form_type_format,
     _form_type_unit_id) = parse_form_type(param_info.form_type)

    if form_type not in settings.MULT_FORM_TYPES: # pragma: no cover - import error
        return None

    key = (param_info.param_qualified_name(), value)
    if key in _PRETTY_MULT_CACHE:
        result = _PRETTY_MULT_CACHE[key]
    else:
        mult_param = get_mult_name(param_info.param_qualified_name())
        model = apps.get_model('search', mult_param.title().replace('_',''))

        results = model.objects.filter(id=value).values('value','label')
        if not results: # pragma: no cover - import error
            return None
        result = results[0]
        _PRETTY_MULT_CACHE[key] = result
    if not cvt_null and result['value'] is None:
        return None
    return result['label']

def lookup_pretty_value_for_mult_list(param_info: ParamInfo, mult_vals: Iterable[Any],
                                      cvt_null: bool) -> str:
    """Given a param_info for a mult list and its values, return the pretty labels.

    Parameters:
        param_info: The field the values belong to.
        mult_vals: What the observation's column holds, which is the ids of rows in
            the field's mult table.
        cvt_null: Whether the mult table's null row should be reported by its label
            rather than as nothing at all.

    Returns:
        The labels of those rows, separated by commas.
    """
    result_list = []
    for mult_val in mult_vals:
        ret = lookup_pretty_value_for_mult(param_info,
                                           mult_val,
                                           cvt_null=cvt_null)
        result_list.append(ret)
    # lookup_pretty_value_for_mult returns None for a mult table's null row when
    # cvt_null is false, and joining a None raises TypeError. That is a real fault
    # rather than a typing artifact, and choosing what a null should display as
    # belongs to the caller that passes cvt_null, so the declaration is left honest
    # and the fault is recorded instead of being cast away.
    return ','.join(result_list) # type: ignore[arg-type]
