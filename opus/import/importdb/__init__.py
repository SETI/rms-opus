from importdb.super import ImportDBException
from importdb.mysql import ImportDBMySQL
# from importdb.postgresql import ImportDBPostgreSQL

def get_db(db_brand, db_hostname, db_name, db_schema,
           db_user, db_password, mult_form_types=None,
           import_prefix=None, logger=None, read_only=False):
    if db_brand.upper() == 'MYSQL':
        return ImportDBMySQL(db_hostname, db_name, db_schema,
                             db_user, db_password,
                             mult_form_types=mult_form_types,
                             import_prefix=import_prefix,
                             logger=logger, read_only=read_only)
    # if db_brand.upper() == 'POSTGRESQL':
    #     return ImportDBPostgreSQL(db_hostname, db_name, db_schema,
    #                               db_user, db_password,
    #                               mult_form_types=mult_form_types,
    #                               import_prefix=import_prefix,
    #                               logger=logger, read_only=read_only)
    if logger:
        logger.log('fatal', f'Unknown database brand "{db_brand}"')
    raise ImportDBException('Unknown database brand '+db_brand)
