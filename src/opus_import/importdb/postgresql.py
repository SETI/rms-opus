"""A placeholder for a PostgreSQL implementation of the pipeline's database interface.

Nothing here is implemented: `ImportDBPostgreSQL` inherits `ImportDBSuper`'s
`NotImplementedError` stubs unchanged, and `opus_import.importdb.get_db` has no branch
that returns it. The module exists so that the brand abstraction has a second brand to
point at, and so that adding one is a matter of filling this in.
"""

from __future__ import annotations

from typing import Any

# import csv
# import psycopg2 as pg
from opus_import.importdb.super import ImportDBSuper


class ImportDBPostgreSQL(ImportDBSuper):
    """The unimplemented PostgreSQL brand."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Record what a connection would need, without opening one.

        Parameters:
            args: Passed to `ImportDBSuper`.
            kwargs: Passed to `ImportDBSuper`.
        """
        super().__init__(*args, **kwargs)
