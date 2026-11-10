"""The version of the database schema this release reads and writes.

Every OPUS table is created by the import from the JSON table schemas that ship with the
release, so a release reads only a schema a release with the same table schemas imported.
`SCHEMA_VERSION` names that generation of the table schemas: a release that changes a
table's columns, keys or contents in a way an earlier release's schema does not have
raises it, and such a release is deployed with a fresh import.

A finished schema records the version that imported it in a one-row table,
``schema_version``, with a state: ``ready`` once the import is finished, ``appending``
while an append to it is in progress. The import's ``--write-schema-version`` step is the
only writer of ``ready``; the web application serves a schema, and both deploy scripts
deploy onto one, only when its row holds this release's version in the ``ready`` state.

This module is imported by the import, by the web application and by the deploy chain's
check, so it imports nothing from Django and nothing that needs a configuration file
until a function here is called.
"""

from __future__ import annotations

from collections.abc import Sequence

#: The generation of the table schemas this release imports and serves.
SCHEMA_VERSION: int = 3

#: The table that holds a schema's version row.
SCHEMA_VERSION_TABLE = 'schema_version'

#: The state of a finished schema, the only one served or deployed onto.
SCHEMA_STATE_READY = 'ready'

#: The state of a schema an append is writing to.
SCHEMA_STATE_APPENDING = 'appending'

#: What makes a schema servable, for the messages that refuse one.
SCHEMA_VERSION_REMEDY = (
    'a schema is served only after an import under this release has finished it with '
    '`opus_import --write-schema-version`'
)


def schema_version_problem(rows: Sequence[Sequence[object]]) -> str | None:
    """Say what keeps a schema with these version rows from being served, if anything.

    Parameters:
        rows: The ``(version, state)`` rows of its ``schema_version`` table; empty when the
            table is absent or empty.

    Returns:
        None when there is exactly one row, holding `SCHEMA_VERSION` in the ``ready``
        state; otherwise a sentence naming what is wrong, followed by `SCHEMA_VERSION_REMEDY`.
    """
    if len(rows) == 0:
        found = f'the schema has no {SCHEMA_VERSION_TABLE} row'
    elif len(rows) > 1:
        found = f'the schema has {len(rows)} {SCHEMA_VERSION_TABLE} rows, not one'
    elif rows[0][0] != SCHEMA_VERSION:
        found = f'the schema is version {rows[0][0]}, and this release is version {SCHEMA_VERSION}'
    elif rows[0][1] != SCHEMA_STATE_READY:
        found = f"the schema's state is {rows[0][1]!r}, not {SCHEMA_STATE_READY!r}"
    else:
        return None
    return f'{found}: {SCHEMA_VERSION_REMEDY}'


def served_schema_version_problem() -> str | None:
    """Say what keeps the schema ``OPUS_CONFIG`` names from being served, for the deploy check.

    The rows are judged by `schema_version_problem`, as the web application judges them, so
    a deploy refuses a schema for exactly the reasons the application would. The connection
    is the import's own, opened read-only, so the check needs nothing the import does not.

    Returns:
        None when the schema may be served; otherwise what `schema_version_problem` says.

    Raises:
        ImportDBError: If the database cannot be read, including when the schema does
            not exist, which the read-only connection does not create.
    """
    from opus_config import get_config
    from opus_import import importdb

    database = get_config().database
    db = importdb.get_db(
        database.brand,
        database.host,
        database.database,
        database.schema,
        database.user,
        database.password,
        read_only=True,
    )
    rows: Sequence[Sequence[object]] = []
    if db.table_exists(SCHEMA_VERSION_TABLE):
        rows = db.read_rows(SCHEMA_VERSION_TABLE, ['version', 'state'])
    return schema_version_problem(rows)
