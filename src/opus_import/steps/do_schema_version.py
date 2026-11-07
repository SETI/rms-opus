"""Record that a schema is finished, in its ``schema_version`` row.

The row says which generation of the table schemas imported the schema
(`opus_import.schema_version.SCHEMA_VERSION`) and whether it is finished. The web
application serves a schema, and the deploy scripts deploy onto one, only when the row
holds the release's version in the ``ready`` state, so this step runs last in every
sequence that finishes a database, after validation.

It writes the version only into a schema that has none: a schema another release
imported is re-imported under this one, never restamped, so a release can never claim a
schema whose tables it did not create.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import import_util
from opus_import.schema_version import (
    SCHEMA_VERSION,
    STATE_APPENDING,
    STATE_READY,
    TABLE_NAME,
)

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def write_schema_version(ctx: ImportContext) -> bool:
    """Mark the permanent schema finished under this release's version.

    Creates the table when it is absent, then:

    * with no row, inserts this release's version in the ``ready`` state;
    * with this version in the ``appending`` state, changes the state to ``ready``,
      logged at info level;
    * with this version already ``ready``, changes nothing, logged at debug level;
    * with any other version, any other state, or more than one row, refuses: an error is
      logged and the table is left as it is.

    Parameters:
        ctx: The import run's context, for the open database and the logger.

    Returns:
        False if it refused, True otherwise.
    """
    db = ctx.db
    assert db is not None
    if db.table_exists('perm', TABLE_NAME):
        rows = db.read_rows('perm', TABLE_NAME, ['version', 'state'])
    else:
        schema = import_util.read_schema_for_table(ctx, TABLE_NAME)
        # schema_version.json is packaged with opus_import, so the schema is always found.
        assert schema is not None
        db.create_table('perm', TABLE_NAME, schema, ignore_if_exists=False)
        rows = []

    if len(rows) == 0:
        db.insert_row('perm', TABLE_NAME, {'version': SCHEMA_VERSION, 'state': STATE_READY})
        import_util.log_info(ctx, f'Schema version {SCHEMA_VERSION} written, {STATE_READY}')
        return True
    if len(rows) > 1:
        found = ', '.join(f'{version} {state}' for version, state in rows)
        import_util.log_error(
            ctx,
            f'The {TABLE_NAME} table holds {len(rows)} rows ({found}) rather than one; '
            'it is left as it is',
        )
        return False

    version, state = rows[0]
    if version != SCHEMA_VERSION:
        import_util.log_error(
            ctx,
            f'The schema is version {version} and this release is version '
            f'{SCHEMA_VERSION}; the row is left as it is. A schema is re-imported under '
            'the release that will serve it, never restamped',
        )
        return False
    if state == STATE_APPENDING:
        db.update_row(
            'perm',
            TABLE_NAME,
            {'state': STATE_READY},
            f'{db.quote_identifier("version")}=%s',
            [SCHEMA_VERSION],
        )
        import_util.log_info(
            ctx, f'Schema version {SCHEMA_VERSION} changed from {STATE_APPENDING} to {STATE_READY}'
        )
        return True
    if state != STATE_READY:
        import_util.log_error(
            ctx, f'The schema version row has the state {state!r}; it is left as it is'
        )
        return False
    import_util.log_debug(ctx, f'Schema version {SCHEMA_VERSION} is already {state}')
    return True
