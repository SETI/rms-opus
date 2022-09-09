################################################################################
#
# tools/db_utils.py
#
################################################################################

from django.apps import apps

from tools.app_utils import get_mult_name

from opus_support import parse_form_type

import settings


MYSQL_TABLE_NOT_EXISTS = 1146
MYSQL_TABLE_ALREADY_EXISTS = 1050
MYSQL_EXECUTION_TIME_EXCEEDED = 3024

def table_model_from_name(table_name):
    "Given a table name (obs_pds) return the Django model class (ObsPds)"
    model_name = ''.join(table_name.title().split('_'))

    # This can throw LookupError
    return apps.get_model('search', model_name)

def query_table_for_opus_id(table_name, opus_id):
    "Return all rows containing opus_id in table_name (better be only one!)"
    # This can throw LookupError
    table_model = table_model_from_name(table_name)
    # opus_id is the primary key for obs_general, but a foreign key for all
    # other tables. Due to Django's design, we have to handle these cases
    # separately.
    if table_name == 'obs_general':
        return table_model.objects.filter(opus_id=opus_id)
    return table_model.objects.filter(obs_general__opus_id=opus_id)

# Looking up entries in the mult tables is slow, so cache them in memory as they
# are retrieved. There aren't that many mult tables or values, so this won't take
# much memory even in the worst case.
_PRETTY_MULT_CACHE = {} # noqa: E305

def lookup_pretty_value_for_mult(param_info, value, cvt_null):
    "Given a param_info for a mult and the mult value, return the pretty label"
    if param_info.form_type is None: # pragma: no cover
        return None

    (form_type, form_type_format,
     form_type_unit_id) = parse_form_type(param_info.form_type)

    if form_type not in settings.MULT_FORM_TYPES: # pragma: no cover
        return None

    key = (param_info.param_qualified_name(), value)
    if key in _PRETTY_MULT_CACHE:
        result = _PRETTY_MULT_CACHE[key]
    else:
        mult_param = get_mult_name(param_info.param_qualified_name())
        model = apps.get_model('search', mult_param.title().replace('_',''))

        results = model.objects.filter(id=value).values('value','label')
        if not results: # pragma: no cover
            return None
        result = results[0]
        _PRETTY_MULT_CACHE[key] = result
    if not cvt_null and result['value'] is None:
        return None
    return result['label']

def lookup_pretty_value_for_mult_list(param_info, mult_vals, cvt_null):
    "Given a param_info for a mult list and the mult list value, return the pretty label"
    result_list = []
    for mult_val in mult_vals:
        ret = lookup_pretty_value_for_mult(param_info,
                                           mult_val,
                                           cvt_null=cvt_null)
        result_list.append(ret)
    return ','.join(result_list)
