"""How the application reads a surface geometry category: as the one table, under its name.

Every surface geometry category's rows are in ``obs_surface_geometry_target``. A body's
category, ``obs_surface_geometry__<target>``, is the rows holding the body's id, and the
selector category, ``obs_surface_geometry_name``, is every row. What is worth pinning,
and why:

* **The category's name stays in the SQL.** Every column reference a search or a results
  page builds is ``<category>.<column>``, so the table is joined under that name, and a
  search naming two bodies joins it twice.
* **A body's join keeps to the body's rows.** Without the body's id in the join, a body's
  columns would read another body's row.
* **The selector never repeats an observation.** An observation with geometry for two
  selected bodies has two rows in the selector's table; its constraint is an ``EXISTS``
  rather than a join, so a search's results hold the observation once.

These stand fakes in for ``table_names``, ``param_info``, ``mult_field`` and ``mult``,
so they run wherever ``pytest`` does.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from django.db.models import Q

from opus_app.apps.paraminfo.models import ParamInfo
from opus_app.apps.search import views as search_views
from opus_app.apps.search.models import (
    Mult,
    MultField,
    ObsGeneral,
    ObsSurfaceGeometryTarget,
    TableNames,
)
from opus_app.apps.tools import db_utils, import_constants, sql_builder
from opus_app.apps.tools.db_utils import resolve_category

#: The selector's field id in the fake ``mult_field``.
TARGET_FIELD_ID = 9

#: The selector's fake ``mult`` rows: id, value, label, disp_rank.
TARGET_ROWS = [(3, 'DIONE', 'Dione', 1), (7, 'SATURN', 'Saturn', 2)]


class _TableNamesManager:
    """Stands in for the manager of ``table_names``."""

    def order_by(self, field: str) -> list[TableNames]:
        """Return the rows, in display order."""
        assert field == 'disp_order'
        rows = [
            ('obs_general', None, None),
            ('obs_surface_geometry_name', 'obs_surface_geometry_target', None),
            ('obs_surface_geometry__dione', 'obs_surface_geometry_target', 3),
            ('obs_surface_geometry__saturn', 'obs_surface_geometry_target', 7),
        ]
        return [
            TableNames(
                table_name=name,
                label=name,
                display='Y',
                disp_order=order,
                physical_table=table,
                target_name=target,
            )
            for order, (name, table, target) in enumerate(rows)
        ]


class _MultRows:
    """The selector field's fake ``mult`` rows."""

    def values_list(self, *fields: str) -> list[tuple[int, str, str, int]]:
        """Return every row."""
        return TARGET_ROWS

    def filter(self, condition: Q) -> Any:
        """Refuse a server lookup: every name asked for is in memory."""
        raise AssertionError('a name was asked of the server')


class _MultManager:
    """Stands in for the manager of ``mult``."""

    def filter(self, *, field_id: int) -> _MultRows:
        """Return the selector's rows."""
        assert field_id == TARGET_FIELD_ID
        return _MultRows()


class _MultFieldManager:
    """Stands in for the manager of ``mult_field``."""

    def values_list(self, *fields: str) -> list[tuple[str, int]]:
        """Name the selector's field."""
        return [('obs_surface_geometry_name.target_name', TARGET_FIELD_ID)]


@pytest.fixture(autouse=True)
def _categories(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Serve the fake tables, starting and ending every test with nothing cached."""

    def clear() -> None:
        import_constants.table_names.cache_clear()
        import_constants.mult_table.cache_clear()
        import_constants._mult_field_ids.cache_clear()
        db_utils._category_tables.cache_clear()
        search_views._PARAMINFO_BY_NAME_CACHE.clear()

    clear()
    monkeypatch.setattr(TableNames, 'objects', _TableNamesManager())
    monkeypatch.setattr(Mult, 'objects', _MultManager())
    monkeypatch.setattr(MultField, 'objects', _MultFieldManager())
    yield
    clear()


def test_a_body_is_its_rows_of_the_one_table_under_its_own_name() -> None:
    """The table, the category's name as its alias, and the body's id."""
    category = resolve_category('obs_surface_geometry__saturn')
    assert category.model is ObsSurfaceGeometryTarget
    assert (category.table, category.alias, category.target_name) == (
        'obs_surface_geometry_target',
        'obs_surface_geometry__saturn',
        7,
    )
    assert not category.is_selector
    source = sql_builder.FromSource(category.source).render()
    assert source == (
        '`obs_surface_geometry_target` AS `obs_surface_geometry__saturn`',
        [],
    )
    condition = category.target_condition()
    assert condition is not None
    assert condition == ('`obs_surface_geometry__saturn`.`target_name` = %s', [7])


def test_the_selector_is_every_row_of_the_one_table() -> None:
    """No body's id, so nothing limits the rows; it is the selector."""
    category = resolve_category('obs_surface_geometry_name')
    assert (category.table, category.target_name) == ('obs_surface_geometry_target', None)
    assert category.is_selector
    assert category.target_condition() is None


def test_a_table_is_its_own_category() -> None:
    """A category with no ``physical_table`` is the table of its name, all of it."""
    category = resolve_category('obs_general')
    assert category.model is ObsGeneral
    assert (category.table, category.alias, category.target_name) == (
        'obs_general',
        'obs_general',
        None,
    )
    assert category.source == 'obs_general'
    assert not category.is_selector


def test_two_bodies_join_the_table_twice_each_on_its_body() -> None:
    """Each join is LEFT, under the body's category, and keeps to the body's rows."""
    from_source = sql_builder.FromSource('obs_general')
    search_views.add_obs_table_joins(
        from_source,
        ['obs_general', 'obs_surface_geometry__dione', 'obs_surface_geometry__saturn'],
    )
    sql, params = from_source.render()
    assert sql == (
        '`obs_general`'
        ' LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__dione`'
        ' ON `obs_general`.`id`=`obs_surface_geometry__dione`.`obs_general_id`'
        ' AND `obs_surface_geometry__dione`.`target_name` = %s'
        ' LEFT JOIN `obs_surface_geometry_target` AS `obs_surface_geometry__saturn`'
        ' ON `obs_general`.`id`=`obs_surface_geometry__saturn`.`obs_general_id`'
        ' AND `obs_surface_geometry__saturn`.`target_name` = %s'
    )
    assert params == [3, 7]


def test_a_search_on_the_selector_is_an_exists_and_joins_nothing() -> None:
    """Two selected bodies cannot repeat an observation that has both."""
    search_views._PARAMINFO_BY_NAME_CACHE[('obs_surface_geometry_name', 'target_name')] = ParamInfo(
        category_name='obs_surface_geometry_name', name='target_name', form_type='GROUP'
    )
    built = search_views._search_select(
        {'obs_surface_geometry_name.target_name': ['Saturn', 'Dione']}, {}
    )
    assert built is not None
    select, _order = built
    select.add_column(sql_builder.column('id', 'obs_general'))
    sql, params = select.build()
    assert sql == (
        'SELECT `obs_general`.`id` FROM `obs_general` WHERE EXISTS (SELECT 1 FROM'
        ' `obs_surface_geometry_target` AS `obs_surface_geometry_name` WHERE'
        ' `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND'
        ' `obs_surface_geometry_name`.`target_name` IN (%s,%s))'
    )
    assert params == [3, 7]


def _selector_param_info() -> None:
    """Serve the selector's ``param_info`` row from the qualified-name cache."""
    search_views._PARAMINFO_BY_NAME_CACHE[('obs_surface_geometry_name', 'target_name')] = ParamInfo(
        category_name='obs_surface_geometry_name', name='target_name', form_type='GROUP'
    )


#: The selector's label for one observation, over the bodies the search selects.
_SELECTED_LABEL = (
    '(SELECT MIN(`mult_obs_surface_geometry_name_target_name`.`label`) FROM'
    ' `obs_surface_geometry_target` AS `obs_surface_geometry_name` LEFT JOIN `mult` AS'
    ' `mult_obs_surface_geometry_name_target_name` ON'
    ' `mult_obs_surface_geometry_name_target_name`.`field_id` = %s AND'
    ' `mult_obs_surface_geometry_name_target_name`.`id`='
    '`obs_surface_geometry_name`.`target_name` WHERE'
    ' `obs_surface_geometry_name`.`obs_general_id`=`obs_general`.`id` AND'
    ' `obs_surface_geometry_name`.`target_name` IN (%s))'
)


def test_sorting_by_the_selector_is_one_label_per_observation_and_joins_nothing() -> None:
    """The sort is the first selected body's label, so no observation is repeated."""
    _selector_param_info()
    terms, mult_tables, obs_tables = search_views.create_order_by_terms(
        ['obs_surface_geometry_name.target_name'],
        [False],
        {'obs_surface_geometry_name.target_name': ['Saturn']},
    )
    assert terms == [(sql_builder.Expr(_SELECTED_LABEL, [TARGET_FIELD_ID, 7]), False)]
    assert (mult_tables, obs_tables) == (set(), set())


def test_without_a_constraint_the_selector_label_reads_every_body() -> None:
    """With no selection of the field, or no search at all, every body counts."""
    every_body = search_views.selector_label('obs_surface_geometry_name', 'target_name', None)
    assert every_body.sql == _SELECTED_LABEL.replace(
        ' AND `obs_surface_geometry_name`.`target_name` IN (%s)', ''
    )
    assert every_body.params == [TARGET_FIELD_ID]
    unconstrained = search_views.selector_label(
        'obs_surface_geometry_name', 'target_name', {'obs_general.planet_id': ['Saturn']}
    )
    assert unconstrained == every_body


def test_a_body_category_keeps_a_statement_to_its_rows() -> None:
    """``restrict`` adds the body's condition; a table of its own adds nothing."""
    body = sql_builder.Select()
    body.add_column(sql_builder.column('phase1', 'obs_surface_geometry__dione'))
    category = resolve_category('obs_surface_geometry__dione')
    body.add_from(category.source)
    category.restrict(body)
    assert body.build() == (
        'SELECT `obs_surface_geometry__dione`.`phase1` FROM `obs_surface_geometry_target` AS'
        ' `obs_surface_geometry__dione` WHERE `obs_surface_geometry__dione`.`target_name` = %s',
        [3],
    )
    table = sql_builder.Select()
    table.add_column(sql_builder.column('id', 'obs_general'))
    table.add_from('obs_general')
    resolve_category('obs_general').restrict(table)
    assert table.build() == ('SELECT `obs_general`.`id` FROM `obs_general`', [])
