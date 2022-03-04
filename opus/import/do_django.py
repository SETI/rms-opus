################################################################################
# do_django.py
#
# Things related to Django and the OPUS UI.
################################################################################

import impglobals
import import_util


def drop_cache_tables():
    import_util.log_debug('Dropping cache tables')
    table_names = impglobals.DATABASE.table_names('all',
                                                  prefix='cache_')
    for table_name in table_names:
        impglobals.DATABASE.drop_table('all', table_name)

    user_search_schema = import_util.read_schema_for_table('user_searches')
    impglobals.DATABASE.drop_table('perm', 'user_searches')
    impglobals.DATABASE.create_table('perm', 'user_searches',
                                     user_search_schema)
