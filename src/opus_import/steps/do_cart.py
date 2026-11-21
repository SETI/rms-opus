"""Create the empty ``cart`` table the web application fills as users select products.

There is nothing to import into it: it starts empty on every run.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def create_cart(ctx: ImportContext) -> None:
    """Drop and re-create the ``cart`` table.

    The table has a foreign key onto ``obs_general``, so it cannot be created before
    that table exists; on a schema without one this logs an error and creates nothing.

    Parameters:
        ctx: The import run's context, for the open database.
    """
    db = ctx.db
    assert db is not None
    if not db.table_exists('obs_general'):
        import_util.log_error(
            ctx, 'Unable to create "cart" table because "obs_general" doesn\'t exist'
        )
        return
    cart_schema = import_util.read_schema_for_table(ctx, 'cart')
    # cart.json is packaged with opus_import, so the schema is always found.
    assert cart_schema is not None
    db.drop_table('cart')
    db.create_table('cart', cart_schema, ignore_if_exists=False)
