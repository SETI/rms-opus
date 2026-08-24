################################################################################
# do_django.py
#
# Things related to Django and the OPUS UI.
################################################################################

from opus_import import import_util


def drop_cache_tables(ctx):
    import_util.log_debug(ctx, 'Dropping cache tables')
    table_names = ctx.db.table_names('all', prefix='cache_')
    for table_name in table_names:
        ctx.db.drop_table('all', table_name)

    user_search_schema = import_util.read_schema_for_table(ctx, 'user_searches')
    ctx.db.drop_table('perm', 'user_searches')
    ctx.db.create_table('perm', 'user_searches', user_search_schema)
