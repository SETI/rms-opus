"""``obs_surface_geometry_target``, and the categories its rows are searched under.

Every body an observation has geometry for is one row of ``obs_surface_geometry_target``,
computed under the body's category, ``obs_surface_geometry__<target>``. What is worth
pinning, and why:

* **One row per body per observation.** The table is keyed by the body and the
  observation, so two names that resolve to one body must write one row, and a name
  that resolves to none must write none.
* **The categories come from the data, in a fixed order.** The rows of ``table_names``,
  ``param_info`` and ``partables`` that the categories derive come out sorted by
  category name, with the same names on every import.
* **Validation reads the table under its categories.** ``param_info`` describes the
  table's columns under the body categories and the selector category, never under the
  table's own name.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from opus_import import config_targets, import_util, surface_geometry
from opus_import.context import ImportContext
from opus_import.obs.obs_surface_geometry_target import ObsSurfaceGeometryTarget
from opus_import.steps import (
    do_import_index,
    do_import_obs,
    do_param_info,
    do_table_names,
    do_validate,
)
from opus_import.surface_geometry import StoredTarget

from .conftest import default_arguments, make_context

#: The surface geometry template, as it is packaged.
_TEMPLATE: list[dict[str, Any]] = json.loads(
    (import_util.TABLE_SCHEMA_DIR / 'obs_surface_geometry_target.json').read_text(encoding='utf-8')
)

# ------------------------------------------------------------------------------------
# One row per body per observation
# ------------------------------------------------------------------------------------


def _emitted(
    bodies: list[tuple[str, Any]], monkeypatch: pytest.MonkeyPatch, *, ignore_errors: bool = False
) -> tuple[list[tuple[str, str]], ImportContext]:
    """Compute one observation's surface geometry rows, returning what was emitted.

    Each row stands for the computation by the category it was computed under and the
    raw name the field functions were told.

    Parameters:
        bodies: Each body's raw name and summary-file row.
        monkeypatch: Replaces the row computation with one recording its inputs.
        ignore_errors: Whether the run has ``--ignore-errors``.

    Returns:
        Each emitted row's table and raw name, and the run's context.
    """
    args = default_arguments()
    args.ignore_errors = ignore_errors
    ctx = make_context(args=args)
    metadata: dict[str, Any] = {}

    def compute(
        _ctx: ImportContext, _obj: Any, table: str, _schema: Any, meta: dict[str, Any]
    ) -> dict[str, Any]:
        return {'raw_name': meta['surface_geo_target_name']}

    monkeypatch.setattr(do_import_obs, 'import_observation_table', compute)
    state = do_import_index.IndexState(
        instrument_obj=ObsSurfaceGeometryTarget(ctx, bundle='TEST_0001', metadata=metadata),
        metadata=metadata,
        base_metadata={},
        table_schemas={},
        table_names_in_order=[],
        pds_version=3,
        obs_rows=[],
    )
    emitted: list[tuple[str, str]] = []
    do_import_index._emit_surface_geometry_rows(
        ctx,
        state,
        _TEMPLATE,
        'co-iss-n1',
        bodies,
        lambda table, row: emitted.append((table, row['raw_name'])),
    )
    return emitted, ctx


def test_each_body_is_one_row_under_its_category(monkeypatch: pytest.MonkeyPatch) -> None:
    """The summary file's spelling picks the row's category, folded onto OPUS's name."""
    emitted, ctx = _emitted([('SATURN', {}), ('K07S4', {})], monkeypatch)
    assert emitted == [
        ('obs_surface_geometry__saturn', 'SATURN'),
        ('obs_surface_geometry__anthe', 'K07S4'),
    ]
    assert ctx.logger.messages_at('warning') == []


def test_two_spellings_of_one_body_write_one_row_and_a_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The first spelling's row is kept; the warning names the observation and both."""
    emitted, ctx = _emitted([('ANTHE', {}), ('K07S4', {})], monkeypatch)
    assert emitted == [('obs_surface_geometry__anthe', 'ANTHE')]
    (warning,) = ctx.logger.messages_at('warning')
    assert 'Observation "co-iss-n1"' in warning
    assert '"ANTHE" and "K07S4", which are both ANTHE' in warning


def test_a_body_no_target_describes_writes_no_row(monkeypatch: pytest.MonkeyPatch) -> None:
    """Its name is reported as unknown, and the observation's other bodies still import."""
    emitted, ctx = _emitted([('NO SUCH BODY', {}), ('SATURN', None)], monkeypatch)
    assert emitted == [('obs_surface_geometry__saturn', 'SATURN')]
    assert any('NO SUCH BODY' in message for message in ctx.logger.messages_at('error'))


def test_two_unknown_bodies_under_ignore_errors_write_one_other_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--ignore-errors`` makes each unknown body OTHER, which one row holds."""
    emitted, ctx = _emitted(
        [('FIRST UNKNOWN', {}), ('SECOND UNKNOWN', {})], monkeypatch, ignore_errors=True
    )
    assert emitted == [('obs_surface_geometry__other', 'FIRST UNKNOWN')]
    (warning,) = ctx.logger.messages_at('warning')
    assert '"FIRST UNKNOWN" and "SECOND UNKNOWN", which are both OTHER' in warning


def test_every_target_reads_its_own_categorys_fields() -> None:
    """A body's category, filled into the template, names the fields after itself.

    The category's fields are the template's entries whose category is the body's, so a
    target whose encoded name the template's substitution spelled differently would have
    no fields at all.
    """
    for target_name in config_targets.TARGET_NAME_INFO:
        if target_name in config_targets.TARGET_NAME_MAPPING:
            # Resolution folds this spelling onto another target, so no row is under it.
            continue
        category = surface_geometry.target_category(import_util.encode_target_name(target_name))
        schema = import_util.read_schema_for_table(make_context(), category)
        assert schema is not None
        assert len(surface_geometry.category_columns(schema, category)) > 1, target_name


def test_the_template_holds_no_string_field() -> None:
    """The string-search choices query a category's table without keeping to one body.

    A string field added to the template needs that query to keep to the body's rows
    first.
    """
    form_types = [str(entry.get('pi_form_type', '')) for entry in _TEMPLATE]
    assert not [form_type for form_type in form_types if form_type.startswith('STRING')]


# ------------------------------------------------------------------------------------
# The categories come from the data
# ------------------------------------------------------------------------------------

#: The bodies the stand-in table holds, out of order.
_TARGETS = [StoredTarget(7, 'saturn'), StoredTarget(3, 'dione')]


def test_the_categories_sort_by_name_among_the_tables() -> None:
    """The bodies' categories sort by name among the tables, before the selector's."""
    tables = ['obs_pds', 'obs_surface_geometry', 'obs_surface_geometry_target', 'obs_type_image']
    assert surface_geometry.category_names(tables, _TARGETS) == [
        'obs_pds',
        'obs_surface_geometry',
        'obs_surface_geometry__dione',
        'obs_surface_geometry__saturn',
        'obs_surface_geometry_name',
        'obs_type_image',
    ]


def test_no_surface_geometry_table_presents_no_surface_geometry_category() -> None:
    """Without the table there is no selector, whatever bodies are passed."""
    assert surface_geometry.category_names(['obs_pds'], _TARGETS) == ['obs_pds']


def test_a_categorys_table_names_row_names_its_table_and_body() -> None:
    """The selector and each body read ``obs_surface_geometry_target``; a table's own row names neither."""
    present = {'obs_general', 'obs_surface_geometry', 'obs_surface_geometry_target'}
    rows = do_table_names.build_table_names_rows(present.__contains__, _TARGETS)
    by_name = {row['table_name']: row for row in rows}
    assert [row['table_name'] for row in rows] == [
        'obs_general',
        'obs_surface_geometry_name',
        'obs_surface_geometry',
        'obs_surface_geometry__dione',
        'obs_surface_geometry__saturn',
    ]
    assert [row['disp_order'] for row in rows] == list(range(5))
    assert by_name['obs_surface_geometry__dione']['label'] == 'Dione Surface Geometry Constraints'
    assert (by_name['obs_surface_geometry__saturn']['physical_table'], 7) == (
        'obs_surface_geometry_target',
        by_name['obs_surface_geometry__saturn']['target_name'],
    )
    assert by_name['obs_surface_geometry_name']['physical_table'] == 'obs_surface_geometry_target'
    assert by_name['obs_surface_geometry_name']['target_name'] is None
    assert (by_name['obs_general']['physical_table'], by_name['obs_general']['target_name']) == (
        None,
        None,
    )


class _CategoryDB:
    """A stand-in schema holding a few tables and two bodies' surface geometry rows."""

    def __init__(self) -> None:
        """Hold the tables; nothing is written yet."""
        self.tables = ['obs_general', 'obs_surface_geometry', 'obs_surface_geometry_target']
        self.inserted: list[dict[str, Any]] = []

    def table_names(self, prefix: str) -> list[str]:
        """Return the tables, sorted."""
        return sorted(name for name in self.tables if name.startswith(prefix))

    def table_exists(self, table_name: str) -> bool:
        """Say whether a table is there."""
        return table_name in self.tables

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[Any, ...]]:
        """Answer the bodies query with each body's id and its selector value."""
        assert params == ['obs_surface_geometry_name.target_name']
        return [(7, 'SATURN'), (3, 'DIONE')]

    def insert_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        """Record what is written."""
        self.inserted += rows


def test_param_info_rows_come_in_the_order_the_tables_gave_them() -> None:
    """The bodies' rows, sorted by body, then the selector's one row.

    ``param_info``'s rows are numbered as they are written, so this order fixes each
    row's id.
    """
    db = _CategoryDB()
    assert do_param_info.fill_param_info(make_context(db=db), 'param_info__new')
    categories = [row['category_name'] for row in db.inserted]
    seen = list(dict.fromkeys(categories))
    assert seen == [
        'obs_general',
        'obs_surface_geometry',
        'obs_surface_geometry__dione',
        'obs_surface_geometry__saturn',
        'obs_surface_geometry_name',
    ]
    selector = [row for row in db.inserted if row['category_name'] == 'obs_surface_geometry_name']
    assert [(row['name'], row['slug']) for row in selector] == [
        ('target_name', 'surfacegeometrytargetname')
    ]
    saturn = [row for row in db.inserted if row['category_name'] == 'obs_surface_geometry__saturn']
    assert len(saturn) == categories.count('obs_surface_geometry__dione')
    assert all(row['slug'].startswith('SURFACEGEOsaturn_') for row in saturn)
    assert 'target_name' not in {row['name'] for row in saturn}


# ------------------------------------------------------------------------------------
# Validation reads the table under its categories
# ------------------------------------------------------------------------------------


class _ValidationDB:
    """A stand-in whose ``param_info`` describes ``obs_surface_geometry_target``'s columns."""

    def __init__(self, body_category: str | None) -> None:
        """Hold the first body category ``param_info`` holds, or None for none."""
        self.body_category = body_category
        self.asked: list[tuple[str, str]] = []

    def table_names(self, prefix: str) -> list[str]:
        """Name ``obs_surface_geometry_target`` alone."""
        return ['obs_surface_geometry_target']

    def quote_identifier(self, name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def table_info(self, table: str) -> list[dict[str, Any]]:
        """Describe the table's key columns and one range pair."""
        return [
            {'field_name': name} for name in ('target_name', 'obs_general_id', 'phase1', 'phase2')
        ]

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[Any, ...]]:
        """Answer the body-category query, then each count by its category and column."""
        if cmd.startswith('MIN('):
            return [(self.body_category,)]
        if 'EXISTS' in cmd or cmd.lstrip().startswith('`g`'):
            return []
        category, name = params
        self.asked.append((category, name))
        described = {
            ('obs_surface_geometry_name', 'target_name'),
            ('obs_surface_geometry__dione', 'phase1'),
            ('obs_surface_geometry__dione', 'phase2'),
        }
        if cmd.lstrip().startswith('`form_type`'):
            return [('RANGE',)] if (category, name) in described else []
        return [(1 if (category, name) in described else 0,)]


def test_param_info_is_checked_under_the_selector_and_a_body_category() -> None:
    """``target_name`` under the selector, every other column under the first body."""
    db = _ValidationDB('obs_surface_geometry__dione')
    ctx = make_context(db=db)
    do_validate.validate_param_info(ctx)
    assert ctx.logger.messages_at('error') == []
    assert db.asked == [
        ('obs_surface_geometry_name', 'target_name'),
        ('obs_surface_geometry__dione', 'phase1'),
        ('obs_surface_geometry__dione', 'phase2'),
    ]


def test_a_pair_is_checked_under_a_body_category() -> None:
    """The order check finds the pair's ``param_info`` row under the first body."""
    db = _ValidationDB('obs_surface_geometry__dione')
    ctx = make_context(db=db)
    do_validate.validate_min_max_order(ctx)
    assert ctx.logger.messages_at('error') == []
    assert ('obs_surface_geometry__dione', 'phase1') in db.asked


def test_an_empty_surface_geometry_table_checks_only_the_selector() -> None:
    """With no body there is no category to describe the geometry columns under."""
    db = _ValidationDB(None)
    ctx = make_context(db=db)
    do_validate.validate_param_info(ctx)
    assert ctx.logger.messages_at('error') == []
    assert db.asked == [('obs_surface_geometry_name', 'target_name')]
