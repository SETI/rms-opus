################################################################################
#
# tools/db_utils.py
#
################################################################################

from django.apps import apps

from tools.app_utils import get_mult_name, parse_form_type

import settings


MYSQL_TABLE_NOT_EXISTS = 1146
MYSQL_TABLE_ALREADY_EXISTS = 1050

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

def lookup_pretty_value_for_mult(param_info, value):
    "Given a param_info for a mult and the mult value, return the pretty label"
    if param_info.form_type is None:
        return None

    (form_type, form_type_func,
     form_type_format) = parse_form_type(param_info.form_type)

    if form_type not in settings.MULT_FORM_TYPES:
        return None

    mult_param = get_mult_name(param_info.param_qualified_name())
    model = apps.get_model('search', mult_param.title().replace('_',''))

    results = model.objects.filter(id=value).values('label')
    if not results:
        return None
    return results[0]['label']
