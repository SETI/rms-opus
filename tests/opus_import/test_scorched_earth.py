"""Scorched earth: every table the import creates goes, in an order the foreign keys allow.

Driven against a stand-in that plants a table of each prefix, every exact name the import
creates, and some of Django's own, and records each drop.
"""

from __future__ import annotations

from opus_import.steps import do_import_tables

from .conftest import make_context

#: Tables ``opus_manage migrate`` creates, which scorched earth leaves.
_DJANGO_TABLES = ('django_session', 'django_migrations', 'auth_user')

#: Every table the import creates by exact name, written out here rather than read from
#: the constant, so that a name dropped from the constant fails these tests.
_EXACT_NAMES = (
    'schema_version',
    'mult',
    'cart',
    'import_bundle',
    'param_info',
    'partables',
    'table_names',
    'contexts',
    'definitions',
    'user_searches',
    'search_results',
    'param_info__new',
    'param_info__old',
    'partables__new',
    'partables__old',
    'table_names__new',
    'table_names__old',
    'contexts__new',
    'contexts__old',
    'definitions__new',
    'definitions__old',
)

#: One table of each prefix the import creates in any number, and the two mult tables
#: the ``mult_`` prefix finds.
_PREFIXED = (
    'obs_general',
    'obs_pds',
    'obs_surface_geometry__saturn',
    'mult_field',
    'mult_group',
)

#: The mult tables, which go last.
_MULT_TABLES = ('mult', 'mult_field', 'mult_group')


class _DroppingDB:
    """A stand-in holding the planted tables, recording every drop."""

    def __init__(self, tables: list[str]) -> None:
        """Hold the tables.

        Parameters:
            tables: The tables the schema holds.
        """
        self.tables = list(tables)
        self.dropped: list[str] = []

    def table_names(self) -> list[str]:
        """Return the tables still there, sorted."""
        return sorted(self.tables)

    def drop_table(self, table_name: str) -> None:
        """Record a drop.

        Parameters:
            table_name: The table.
        """
        self.tables.remove(table_name)
        self.dropped.append(table_name)


def _erase(tables: list[str]) -> _DroppingDB:
    """Run scorched earth over a schema holding `tables`, returning the stand-in."""
    db = _DroppingDB(tables)
    do_import_tables.delete_all_opus_tables(make_context(db=db))
    return db


def test_every_opus_table_goes_and_no_django_table_does() -> None:
    """The prefixes and the exact names cover every table the import creates."""
    db = _erase([*_PREFIXED, *_EXACT_NAMES, *_DJANGO_TABLES])
    assert sorted(db.tables) == sorted(_DJANGO_TABLES)
    assert sorted(db.dropped) == sorted([*_PREFIXED, *_EXACT_NAMES])


def test_the_drop_order_follows_the_foreign_keys() -> None:
    """The version table first, children before cart before obs_general, mult tables last."""
    db = _erase([*_PREFIXED, *_EXACT_NAMES, *_DJANGO_TABLES])
    position = {table: index for index, table in enumerate(db.dropped)}
    assert db.dropped[0] == 'schema_version'
    assert position['obs_pds'] < position['cart'] < position['obs_general']
    assert position['obs_surface_geometry__saturn'] < position['cart']
    for definitions in ('definitions', 'definitions__new', 'definitions__old'):
        assert position['obs_general'] < position[definitions] < position['contexts']
    assert sorted(db.dropped[-len(_MULT_TABLES) :]) == sorted(_MULT_TABLES)
    for mult_table in _MULT_TABLES:
        assert position['obs_general'] < position[mult_table]
        assert position['import_bundle'] < position[mult_table]
        assert position['search_results'] < position[mult_table]


def test_an_absent_table_is_not_asked_for() -> None:
    """Only the tables the schema holds are dropped."""
    db = _erase(['obs_general', 'auth_user'])
    assert db.dropped == ['obs_general']
