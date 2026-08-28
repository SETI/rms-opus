"""Create the empty ``cart`` table the web application fills as users select products.

The table is created directly in the permanent namespace, because there is nothing to
import into it -- it starts empty on every run.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opus_import import import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def create_cart(ctx: ImportContext) -> None:
    """Drop and re-create the permanent ``cart`` table, if that is possible yet.

    The table has a foreign key onto ``obs_general``, so it cannot be created before
    that table exists -- and it has to be emptied before ``obs_general`` is rebuilt, or
    the rebuild trips the constraint. When ``obs_general`` is missing, this records on
    the context that the attempt is worth repeating and returns; `opus_import.cli` makes
    the second attempt after the import. A second failure is an error, because by then
    the import should have created ``obs_general``.

    Parameters:
        ctx: The import run's context, for the open database and the retry flag.
    """
    # There's really no point in doing this as an import table first,
    # since we're just creating an empty table.
    db = ctx.db
    assert db is not None
    if not db.table_exists('perm', 'obs_general'):
        # We can't create cart here, because it has a foreign key
        # constraint on obs_general. But we needed to have tried because we
        # need to be able to delete things from obs_general and have
        # cart be empty! Chicken and egg.
        # So what we do is check here to see if obs_general exists. If it does,
        # we can go ahead and remove and re-create cart. If it doesn't,
        # then we don't do anything right now but set a flag to say that we'll
        # try again at the end of the import.
        if ctx.try_cart_later:
            # Oops! We've already been down this road once, and apparently the
            # creation of obs_general failed. So we can't do anything.
            import_util.log_error(
                ctx, 'Unable to create "cart" table because "obs_general" doesn\'t exist'
            )
            return
        ctx.try_cart_later = True
        import_util.log_warning(
            ctx,
            'Unable to create "cart" table because "obs_general" doesn\'t exist'
            + ' - Will try again later',
        )
        return
    cart_schema = import_util.read_schema_for_table(ctx, 'cart')
    # cart.json is packaged with opus_import, so the schema is always found.
    assert cart_schema is not None
    db.drop_table('perm', 'cart')
    db.create_table('perm', 'cart', cart_schema, ignore_if_exists=False)
