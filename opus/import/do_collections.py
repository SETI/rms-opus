################################################################################
# do_collections.py
#
# Create an empty collections table.
################################################################################

import os

from config_data import *
import impglobals
import import_util


def create_collections():
    # There's really no point in doing this as an import table first,
    # since we're just creating an empty table.
    db = impglobals.DATABASE
    collections_schema = import_util.read_schema_for_table('collections')
    db.drop_table('perm', 'collections')
    db.create_table('perm', 'collections', collections_schema,
                    ignore_if_exists=False)
