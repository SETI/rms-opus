"""The import pipeline's database layer, one module per database brand.

`get_db` is the only way the pipeline opens a database: it dispatches on the brand named
in the configuration and returns an `opus_import.importdb.super.ImportDBSuper`, so no
step module names a brand. MySQL is the only brand implemented;
`opus_import.importdb.postgresql` is a stub kept so that adding a second one is a matter
of filling it in and adding a branch here.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from opus_config.config import DEFAULT_TRANSACTION_ROWS
from opus_import.importdb.mysql import ImportDBMySQL
from opus_import.importdb.super import ImportDBError

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pdslogger

    from opus_import.importdb.super import ImportDBSuper

# from importdb.postgresql import ImportDBPostgreSQL

# The package's surface: the pipeline opens a database with `get_db`, names a
# server-wide lock with `lock_name`, and catches `ImportDBError`. The brand classes are
# reached through their own modules.
__all__ = ['ImportDBError', 'get_db', 'lock_name']

#: What every lock name `lock_name` returns starts with.
LOCK_NAME_PREFIX = 'opus:'


def lock_name(schema: str, *parts: object) -> str:
    """Return the name of a server-wide named lock belonging to one schema.

    The name is `LOCK_NAME_PREFIX` followed by the hexadecimal SHA-1 of the schema and
    the parts, joined by ``:``, so it fits MySQL's 64-character limit on a lock name
    whatever the schema is called, and two schemas never share a lock.

    Parameters:
        schema: The schema the lock guards.
        parts: What the lock is for within the schema, such as ``'register'``; each is
            rendered with ``str``.

    Returns:
        The lock's name.
    """
    joined = ':'.join([schema, *(str(part) for part in parts)])
    # SHA-1 makes a short, fixed-length name here, not a security property.
    digest = hashlib.sha1(joined.encode('utf-8'), usedforsecurity=False).hexdigest()
    return LOCK_NAME_PREFIX + digest


def get_db(
    db_brand: str,
    db_hostname: str,
    db_name: str,
    db_schema: str,
    db_user: str,
    db_password: str,
    mult_form_types: Sequence[str] | None = None,
    logger: pdslogger.PdsLogger | None = None,
    read_only: bool = False,
    bulk_load: bool = True,
    scratch_dir: str | None = None,
    transaction_rows: int = DEFAULT_TRANSACTION_ROWS,
) -> ImportDBSuper:
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
        mult_form_types: The ``param_info`` form types whose columns hold mult ids, or
            None for none of them.
        logger: Where to report progress, statements and warnings, or None to report
            nothing.
        read_only: True to log every mutating statement instead of executing it.
        bulk_load: Whether rows may be bulk loaded from a scratch file, the
            configuration's ``[import] bulk_load``.
        scratch_dir: The directory the scratch files go in, or None for the system
            temporary directory; the configuration's ``[import] scratch_dir``.
        transaction_rows: The most rows one bulk load writes in one transaction; the
            configuration's ``[import] transaction_rows``.

    Returns:
        An open connection to the database, ready for the pipeline to use.

    Raises:
        ImportDBError: If the brand is not one this package implements, or the
            connection cannot be opened.
        ValueError: If `transaction_rows` is less than 1.
    """
    if db_brand.upper() == 'MYSQL':
        return ImportDBMySQL(
            db_hostname,
            db_name,
            db_schema,
            db_user,
            db_password,
            mult_form_types=mult_form_types,
            logger=logger,
            read_only=read_only,
            bulk_load=bulk_load,
            scratch_dir=scratch_dir,
            transaction_rows=transaction_rows,
        )
    # if db_brand.upper() == 'POSTGRESQL':
    #     return ImportDBPostgreSQL(db_hostname, db_name, db_schema,
    #                               db_user, db_password,
    #                               mult_form_types=mult_form_types,
    #                               logger=logger, read_only=read_only)
    if logger:
        logger.log('fatal', f'Unknown database brand "{db_brand}"')
    raise ImportDBError('Unknown database brand ' + db_brand)
