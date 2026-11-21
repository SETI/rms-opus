"""Carry the served schema's sessions and carts over into the schema a deploy promotes.

A full-import deploy serves a new schema, whose ``django_session`` and ``cart`` tables
start empty, so without this every visitor would lose the cart they had built. The step
runs while the web service is stopped, between the old schema's last request and the new
one's first, with the new schema as the import's target: the served schema's unexpired
sessions that own a cart row are copied, and each cart row whose observation the new
schema still holds, by OPUS ID, under the new schema's id for it. A cart row whose
session expired or whose observation is gone is dropped and counted. A session holds
nothing else a visitor would miss (``has_session``, and the download quota
``cum_download_size``, which starts again; a staff member signed in to Django's admin
signs in again), so the sessions without a cart, one for every cookieless API caller,
are not copied while the site is down. The target's two
tables are emptied and filled in one transaction, so a failure leaves them as they were,
the step can run again, and it runs in either direction: going back to the previous
schema is a promotion toward it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import import_util
from opus_import.importdb import ImportDBError

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def carry_over_sessions(ctx: ImportContext, source_schema: str) -> bool:
    """Replace the target schema's sessions and cart rows with the served schema's.

    Parameters:
        ctx: The import run's context, for the open database.
        source_schema: The schema being served, which is only read.

    Returns:
        True when the copy committed; False when it failed, which is logged.
    """
    db = ctx.db
    assert db is not None
    import_util.log_info(
        ctx, f'Carrying sessions and carts over from {source_schema} into {db.db_schema}'
    )
    try:
        carried = db.carry_over_sessions(source_schema)
    except ImportDBError:
        return False
    import_util.log_info(
        ctx,
        f'Carried over {carried.sessions} sessions and {carried.cart_rows} cart rows; '
        f'dropped {carried.dropped_cart_rows} of the {carried.source_cart_rows} cart rows '
        'whose session expired or whose observation this schema lacks',
    )
    return True
