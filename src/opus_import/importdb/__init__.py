"""The import pipeline's database layer, one module per database brand.

`get_db` is the only way the pipeline opens a database: it dispatches on the brand named
in the configuration and returns an `opus_import.importdb.super.ImportDBSuper`, so no
step module names a brand. MySQL is the only brand implemented;
`opus_import.importdb.postgresql` is a stub kept so that adding a second one is a matter
of filling it in and adding a branch here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import.importdb.mysql import ImportDBMySQL
from opus_import.importdb.super import ImportDBError

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pdslogger

    from opus_import.importdb.super import ImportDBSuper

# from importdb.postgresql import ImportDBPostgreSQL

# The package's surface: the pipeline opens a database with `get_db` and catches
# `ImportDBError`. The brand classes are reached through their own modules.
__all__ = ['ImportDBError', 'get_db']


def get_db(db_brand: str, db_hostname: str, db_name: str, db_schema: str,
           db_user: str, db_password: str,
           mult_form_types: Sequence[str] | None = None,
           import_prefix: str | None = None,
           logger: pdslogger.PdsLogger | None = None,
           read_only: bool = False) -> ImportDBSuper:
    """Open a database of the named brand.

    Parameters:
        db_brand: The brand, matched without regard to case. ``'MySQL'`` is the only one
            implemented.
        db_hostname: The database server's host name.
        db_name: The database name. MySQL has no such concept above the schema and
            ignores it.
        db_schema: The schema (MySQL database) holding the OPUS tables.
        db_user: The user to connect as.
        db_password: That user's password.
        mult_form_types: The ``param_info`` form types that have a ``mult_`` table, or
            None for none of them.
        import_prefix: The prefix distinguishing an import table from its permanent
            counterpart, or None to make the two namespaces the same tables.
        logger: Where to report progress, statements and warnings, or None to report
            nothing.
        read_only: True to log every mutating statement instead of executing it.

    Returns:
        An open connection to the database, ready for the pipeline to use.

    Raises:
        ImportDBError: If the brand is not one this package implements, or the
            connection cannot be opened.
    """
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
    raise ImportDBError('Unknown database brand '+db_brand)
