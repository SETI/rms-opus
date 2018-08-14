from django.apps import apps

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
