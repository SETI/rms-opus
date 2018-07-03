from django.apps import apps

def table_model_from_name(table_name):
    model_name = ''.join(table_name.title().split('_'))

    # This can throw LookupError
    return apps.get_model('search', model_name)

def query_table_for_opus_id(table_name, opus_id):
    # This can throw LookupError
    table_model = table_model_from_name(table_name)
    if table_name == 'obs_general':
        return table_model.objects.filter(opus_id=opus_id)
    return table_model.objects.filter(obs_general__opus_id=opus_id)
