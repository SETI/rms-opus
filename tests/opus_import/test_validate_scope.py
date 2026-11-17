"""Tests for validation while a generation is pending: what each check reads, against
stand-ins.

Each check's statements are recorded by a stand-in database. With a generation pending
they read the rows the update wrote (`validation_queries.GenerationScope`); with none
while the rows the last switch retired await the purge, the served generation's
(`validation_queries.served_generation_only`); otherwise every row, with no condition and
no value.
"""

from __future__ import annotations

from typing import Any

import pytest

from opus_import import bundle_registry, validation_queries
from opus_import.context import ImportContext
from opus_import.generations import GenerationState
from opus_import.schema_version import SCHEMA_STATE_READY, SCHEMA_VERSION
from opus_import.steps import do_validate

from .conftest import make_context

#: The pending generation of the cases.
_PENDING = 2

#: The registry rows of the cases, as ``(bundle_number, bundle_id, size_estimate, first_id,
#: id_capacity, state, started_at, generation)``: the served generation's copies of a
#: bundle the pending generation re-imports and of one it drops, both retired, and the
#: pending generation's copy of the first.
_REGISTRY = [
    (1, 'COISS_2002', 10, 0, 1000, 'done', None, 1),
    (2, 'COISS_2008', 5, 1000, 500, 'done', None, 1),
    (3, 'COISS_2002', 10, 1500, 1000, 'done', None, _PENDING),
]

#: The bundle numbers of the rows the pending generation retired.
_RETIRED = {1, 2}

#: The first id after every range the served generation registered.
_FIRST_ID = 1500


class _ScopeDB:
    """A stand-in schema of a few observation tables, recording every select.

    Attributes:
        tables: The tables, each with its columns.
        registry: The registry rows `read_rows` returns, or None for no registry.
        groups: The rows a ``DISTINCT`` select returns.
        count: The figure a ``COUNT`` select returns.
        selects: Every select, its whitespace collapsed, with its values.
        compared: The arguments of every junction comparison.
    """

    def __init__(
        self,
        tables: dict[str, list[str]],
        registry: list[tuple[Any, ...]] | None = None,
        groups: list[tuple[Any, ...]] | None = None,
    ) -> None:
        """Hold the tables, the registry and the filters the generation carries."""
        self.tables = tables
        self.registry = registry
        self.groups = [] if groups is None else groups
        self.count = 0
        self.selects: list[tuple[str, list[Any] | None]] = []
        self.compared: list[tuple[Any, ...]] = []

    @staticmethod
    def quote_identifier(name: str) -> str:
        """Backtick-quote a name."""
        return f'`{name}`'

    def forget_table_names(self) -> None:
        """Hold nothing to forget."""

    def table_names(self, prefix: str) -> list[str]:
        """Return the observation tables."""
        return [name for name in self.tables if name.startswith(prefix)]

    def table_exists(self, table: str) -> bool:
        """Hold the tables given, and the registry when it has rows to give."""
        if table == bundle_registry.BUNDLE_REGISTRY_TABLE:
            return self.registry is not None
        return table in self.tables

    def table_info(self, table: str) -> list[dict[str, Any]]:
        """Describe a table's columns, every one nullable."""
        return [{'field_name': name, 'field_notnull': False} for name in self.tables[table]]

    def read_rows(
        self, table: str, columns: Any, where: Any = None, params: Any = None
    ) -> list[tuple[Any, ...]]:
        """Return the registry's rows: every one for a selection that admits retired rows,
        and the live ones otherwise."""
        assert table == bundle_registry.BUNDLE_REGISTRY_TABLE
        assert self.registry is not None
        if str(where).startswith('1=1'):
            return list(self.registry)
        return [row for row in self.registry if row[0] not in _RETIRED]

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[Any, ...]]:
        """Record the select; give the filters for a ``DISTINCT``, the count for a
        ``COUNT``, one NULL for each column a ``SUM`` counts, a range for ``form_type``,
        and no row otherwise."""
        flat = ' '.join(cmd.split())
        self.selects.append((flat, None if params is None else list(params)))
        if flat.startswith('DISTINCT'):
            return list(self.groups)
        if flat.startswith('COUNT('):
            return [(self.count,)]
        if flat.startswith('SUM('):
            return [(1,) * flat.count('SUM(')]
        if flat.startswith('`form_type`'):
            return [('RANGE',)]
        return []

    def list_junction_mismatches(self, *arguments: Any) -> tuple[int, int | None]:
        """Record the comparison and find no disagreement."""
        self.compared.append(arguments)
        return 0, None


def _pending(db: _ScopeDB) -> ImportContext:
    """Return a context writing the pending generation on a stand-in."""
    ctx = make_context(db=db)
    ctx.generation_state = GenerationState(
        SCHEMA_VERSION, SCHEMA_STATE_READY, 1, _PENDING, 'finalized', False
    )
    ctx.import_generation = _PENDING
    return ctx


def _served(db: _ScopeDB) -> ImportContext:
    """Return a context with no generation pending on a stand-in."""
    return make_context(db=db)


#: The generation served after the switch of the revertible cases.
_SWITCHED = 2


def _revertible(db: _ScopeDB) -> ImportContext:
    """Return a context serving a switched-in generation whose retired rows remain."""
    ctx = make_context(db=db)
    ctx.generation_state = GenerationState(
        SCHEMA_VERSION, SCHEMA_STATE_READY, _SWITCHED, None, None, True
    )
    ctx.import_generation = _SWITCHED
    return ctx


#: The condition that an ``obs_general`` row aliased ``g`` is one the generation added.
_ADDED = '`g`.`id` >= %s AND `g`.`added_generation` = %s'

#: The condition that an ``obs_general`` row aliased ``g`` is in a generation.
_IN_GENERATION = (
    '`g`.`added_generation` <= %s AND (`g`.`removed_generation` IS NULL OR '
    '`g`.`removed_generation` > %s)'
)


# ------------------------------------------------------------------------------------
# The scope
# ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('registry', 'first_id'),
    [(_REGISTRY, _FIRST_ID), (_REGISTRY[2:], 0), (None, 0)],
)
def test_the_scope_starts_after_every_earlier_generations_range(
    registry: list[tuple[Any, ...]] | None, first_id: int
) -> None:
    """A retired row's range counts; the pending generation's own rows do not."""
    db = _ScopeDB({}, registry)
    assert bundle_registry.end_before_generation(db, _PENDING) == first_id  # type: ignore[arg-type]


def test_no_pending_generation_has_no_scope() -> None:
    """Every row is read when no generation is pending."""
    db = _ScopeDB({}, _REGISTRY)
    assert validation_queries.generation_scope(_served(db)) is None
    assert validation_queries.generation_scope(_pending(db)) == validation_queries.GenerationScope(
        _PENDING, _FIRST_ID
    )


@pytest.mark.parametrize(
    ('pending', 'revertible', 'served'),
    [(None, True, _SWITCHED), (None, False, None), (3, False, None), (3, True, None)],
)
def test_only_the_served_generation_is_read_while_retired_rows_remain(
    pending: int | None, revertible: bool, served: int | None
) -> None:
    """From a switch until the purge, with no generation pending; never otherwise."""
    ctx = make_context(db=_ScopeDB({}))
    assert validation_queries.served_generation_only(ctx) is None
    ctx.generation_state = GenerationState(
        SCHEMA_VERSION,
        SCHEMA_STATE_READY,
        _SWITCHED,
        pending,
        None if pending is None else 'writing',
        revertible,
    )
    assert validation_queries.served_generation_only(ctx) == served


def test_the_scopes_conditions_read_the_keys() -> None:
    """The observations by primary key and generation, their rows by observation id."""
    scope = validation_queries.GenerationScope(_PENDING, _FIRST_ID)
    q = _ScopeDB.quote_identifier
    assert scope.added(q, 'g') == (_ADDED, [_FIRST_ID, _PENDING])
    assert scope.children(q, 'c') == ('`c`.`obs_general_id` >= %s', [_FIRST_ID])


# ------------------------------------------------------------------------------------
# The per-row checks
# ------------------------------------------------------------------------------------

_TABLES = {
    'obs_general': ['id', 'opus_id', 'time1', 'time2'],
    'obs_pds': ['obs_general_id', 'bundle_id', 'note'],
    'obs_preview': ['obs_general_id'],
    'obs_ring_geometry': ['obs_general_id', 'phase1', 'phase2'],
}


def test_min_max_reads_the_generations_rows_while_it_is_pending() -> None:
    """``obs_general`` by its primary key, a child by its observation id as well."""
    db = _ScopeDB(_TABLES | {'param_info__new': []}, _REGISTRY)
    do_validate.validate_min_max_order(_pending(db))
    scanned = [select for select in db.selects if 'opus_id' in select[0]]
    assert scanned == [
        (
            '`g`.`opus_id` FROM `obs_general` `g` WHERE `g`.`time2` < `g`.`time1` AND ' + _ADDED,
            [_FIRST_ID, _PENDING],
        ),
        (
            '`g`.`opus_id` FROM `obs_ring_geometry` `c` JOIN `obs_general` `g` ON `g`.`id` = '
            '`c`.`obs_general_id` WHERE `c`.`phase2` < `c`.`phase1` AND '
            '`c`.`obs_general_id` >= %s AND ' + _ADDED,
            [_FIRST_ID, _FIRST_ID, _PENDING],
        ),
    ]


def test_min_max_reads_every_row_with_no_generation_pending() -> None:
    """The statements carry no condition and no value."""
    db = _ScopeDB(_TABLES | {'param_info': []}, _REGISTRY)
    do_validate.validate_min_max_order(_served(db))
    scanned = [select for select in db.selects if 'opus_id' in select[0]]
    assert scanned == [
        ('`opus_id` FROM `obs_general` WHERE `time2` < `time1`', None),
        (
            '`g`.`opus_id` FROM `obs_ring_geometry` `c` JOIN `obs_general` `g` ON `g`.`id` = '
            '`c`.`obs_general_id` WHERE `c`.`phase2` < `c`.`phase1`',
            None,
        ),
    ]


def test_min_max_reads_the_served_generation_while_retired_rows_remain() -> None:
    """``obs_general`` and a child, each kept to the served generation's observations."""
    db = _ScopeDB(_TABLES | {'param_info': []}, _REGISTRY)
    do_validate.validate_min_max_order(_revertible(db))
    scanned = [select for select in db.selects if 'opus_id' in select[0]]
    assert scanned == [
        (
            '`g`.`opus_id` FROM `obs_general` `g` WHERE `g`.`time2` < `g`.`time1` AND '
            + _IN_GENERATION,
            [_SWITCHED, _SWITCHED],
        ),
        (
            '`g`.`opus_id` FROM `obs_ring_geometry` `c` JOIN `obs_general` `g` ON `g`.`id` = '
            '`c`.`obs_general_id` WHERE `c`.`phase2` < `c`.`phase1` AND ' + _IN_GENERATION,
            [_SWITCHED, _SWITCHED],
        ),
    ]


def test_orphans_are_counted_against_every_row_while_retired_rows_remain() -> None:
    """A retired observation's rows are not orphans, so the statements carry no condition."""
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_orphans(_revertible(db))
    assert [values for _cmd, values in db.selects] == [None, None, None]


def test_orphans_are_counted_by_their_own_observation_id_while_pending() -> None:
    """An orphan has no obs_general row to select it by, so it is chosen by its own id."""
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_orphans(_pending(db))
    anti_join = (
        'COUNT(*) FROM `{0}` LEFT JOIN `obs_general` ON `{0}`.`obs_general_id` = '
        '`obs_general`.`id` WHERE `obs_general`.`id` IS NULL'
    )
    assert db.selects == [
        (anti_join.format(name) + f' AND `{name}`.`obs_general_id` >= %s', [_FIRST_ID])
        for name in ('obs_pds', 'obs_preview', 'obs_ring_geometry')
    ]
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_orphans(_served(db))
    assert db.selects == [
        (anti_join.format(name), None) for name in ('obs_pds', 'obs_preview', 'obs_ring_geometry')
    ]


def test_obs_pds_is_compared_for_the_generations_rows_while_pending() -> None:
    """The child by its observation id, the observation by its key and generation."""
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_pds_bundle_ids(_pending(db))
    compared = (
        'COUNT(*) FROM `obs_pds` `p` JOIN `obs_general` `g` ON `g`.`id` = `p`.`obs_general_id` '
        'WHERE `p`.`bundle_id` <> `g`.`bundle_id`'
    )
    assert db.selects == [
        (
            f'{compared} AND `p`.`obs_general_id` >= %s AND {_ADDED}',
            [_FIRST_ID, _FIRST_ID, _PENDING],
        )
    ]
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_pds_bundle_ids(_served(db))
    assert db.selects == [(compared, None)]
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_pds_bundle_ids(_revertible(db))
    assert db.selects == [(f'{compared} AND {_IN_GENERATION}', [_SWITCHED, _SWITCHED])]


def test_previews_are_counted_for_the_generations_observations_while_pending() -> None:
    """Only the observations the generation added are anti-joined."""
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_previews(_pending(db))
    counted = (
        'COUNT(*) FROM `obs_general` `g` LEFT JOIN `obs_preview` `p` ON `p`.`obs_general_id` = '
        '`g`.`id` WHERE `p`.`obs_general_id` IS NULL'
    )
    assert db.selects == [(f'{counted} AND {_ADDED}', [_FIRST_ID, _PENDING])]
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_previews(_served(db))
    assert db.selects == [(counted, None)]
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_previews(_revertible(db))
    assert db.selects == [(f'{counted} AND {_IN_GENERATION}', [_SWITCHED, _SWITCHED])]


@pytest.mark.parametrize(('pending', 'first_id'), [(True, _FIRST_ID), (False, None)])
def test_junctions_are_compared_from_the_scopes_first_id(
    pending: bool, first_id: int | None
) -> None:
    """The comparison is handed the scope's first id, or none with no generation pending."""
    db = _ScopeDB({'obs_general': [], 'obs_general_target_name': []}, _REGISTRY)
    ctx = _pending(db) if pending else _served(db)
    do_validate.validate_junctions(ctx)
    assert ('obs_general', 'target_name', 'obs_general_target_name', 'id', first_id) in db.compared


# ------------------------------------------------------------------------------------
# The filter check
# ------------------------------------------------------------------------------------

#: The least and greatest of every wavelength column, as the filter query selects them.
_RANGES = ', '.join(
    f"MIN(IFNULL(`w`.`{name}`, 'NULL')), MAX(IFNULL(`w`.`{name}`, 'NULL'))"
    for name in validation_queries.WAVELENGTH_FIELDS
)

#: The join of an instrument table, aliased ``c``, to its wavelength rows.
_WAVELENGTHS = 'LEFT JOIN `obs_wavelength` `w` ON `c`.`obs_general_id` = `w`.`obs_general_id`'


def test_the_filters_the_generation_carries_are_compared_across_its_live_rows() -> None:
    """Cassini ISS by camera and filter, NULL included; every live row of the generation
    is compared, served or its own, and a retired one is not."""
    tables = {'obs_instrument_coiss': ['obs_general_id', 'camera', 'combined_filter']}
    db = _ScopeDB(tables, _REGISTRY, groups=[('N', 'CL1'), ('W', None)])
    do_validate.validate_filter_wavelength_consistency(_pending(db))
    carried, grouped = db.selects
    assert carried == (
        'DISTINCT `c`.`camera`, `c`.`combined_filter` FROM `obs_instrument_coiss` `c` JOIN '
        '`obs_general` `g` ON `g`.`id` = `c`.`obs_general_id` WHERE `c`.`obs_general_id` >= %s '
        f'AND {_ADDED}',
        [_FIRST_ID, _FIRST_ID, _PENDING],
    )
    match = '(`c`.`camera` <=> %s AND `c`.`combined_filter` <=> %s)'
    assert grouped == (
        f'`c`.`camera`, `c`.`combined_filter`, {_RANGES} FROM `obs_instrument_coiss` `c` JOIN '
        f'`obs_general` `g` ON `g`.`id` = `c`.`obs_general_id` {_WAVELENGTHS} WHERE '
        '`g`.`added_generation` <= %s AND (`g`.`removed_generation` IS NULL OR '
        f'`g`.`removed_generation` > %s) AND ({match} OR {match}) '
        'GROUP BY `c`.`camera`, `c`.`combined_filter`',
        [_PENDING, _PENDING, 'N', 'CL1', 'W', None],
    )


def test_a_table_the_generation_added_nothing_to_is_not_compared() -> None:
    """With no filter among the generation's rows, only the search for them runs."""
    db = _ScopeDB({'obs_instrument_vgiss': ['obs_general_id', 'filter_name']}, _REGISTRY)
    do_validate.validate_filter_wavelength_consistency(_pending(db))
    assert [select[0].split()[0] for select in db.selects] == ['DISTINCT']


def test_every_filter_is_compared_with_no_generation_pending() -> None:
    """One grouped statement over the whole table, with no condition."""
    db = _ScopeDB({'obs_instrument_vgiss': ['obs_general_id', 'filter_name']}, _REGISTRY)
    do_validate.validate_filter_wavelength_consistency(_served(db))
    assert db.selects == [
        (
            f'`c`.`filter_name`, {_RANGES} FROM `obs_instrument_vgiss` `c` {_WAVELENGTHS} '
            'GROUP BY `c`.`filter_name`',
            None,
        )
    ]


def test_every_served_filter_is_compared_while_retired_rows_remain() -> None:
    """One grouped statement over the served generation's observations, so a filter the
    update corrected is not compared with its retired rows."""
    db = _ScopeDB({'obs_instrument_vgiss': ['obs_general_id', 'filter_name']}, _REGISTRY)
    do_validate.validate_filter_wavelength_consistency(_revertible(db))
    assert db.selects == [
        (
            f'`c`.`filter_name`, {_RANGES} FROM `obs_instrument_vgiss` `c` JOIN `obs_general` '
            f'`g` ON `g`.`id` = `c`.`obs_general_id` {_WAVELENGTHS} WHERE {_IN_GENERATION} '
            'GROUP BY `c`.`filter_name`',
            [_SWITCHED, _SWITCHED],
        )
    ]


class _FilterRowDB(_ScopeDB):
    """A stand-in whose grouped filter query returns one disagreeing row."""

    def general_select(self, cmd: str, params: Any = None) -> list[tuple[Any, ...]]:
        """Give the generation's filter, then a group whose first wavelength disagrees."""
        rows = super().general_select(cmd, params)
        if cmd.startswith('`c`'):
            agreeing = [0.5, 0.5] * (len(validation_queries.WAVELENGTH_FIELDS) - 1)
            return [('CLEAR', 0.4, 0.7, *agreeing)]
        return rows


def test_a_disagreeing_filter_is_a_warning_naming_the_column_and_values() -> None:
    """The column, the table, the filter and both values are named."""
    db = _FilterRowDB(
        {'obs_instrument_vgiss': ['obs_general_id', 'filter_name']}, _REGISTRY, [('CLEAR',)]
    )
    ctx = _pending(db)
    do_validate.validate_filter_wavelength_consistency(ctx)
    assert ctx.logger.messages_at('warning') == [
        '"obs_wavelength.wavelength1" has inconsistent values for obs_instrument_vgiss filter '
        '"CLEAR": 0.4 and 0.7'
    ]


# ------------------------------------------------------------------------------------
# The NULL check, the OPUS IDs, and the run
# ------------------------------------------------------------------------------------


def test_the_null_check_is_skipped_and_says_so_while_pending() -> None:
    """It describes the schema, which a few bundles cannot show."""
    db = _ScopeDB(_TABLES, _REGISTRY)
    ctx = _pending(db)
    do_validate.validate_nulls(ctx)
    assert db.selects == []
    assert ctx.logger.messages_at('info') == [
        f'Not checking for nullable columns that hold no NULL in generation {_PENDING}: the '
        'check describes the whole schema'
    ]


def test_the_null_check_counts_the_served_generation_while_retired_rows_remain() -> None:
    """``obs_general`` by its own generation columns, a child through its observation."""
    db = _ScopeDB(
        {'obs_general': ['id', 'time1'], 'obs_ring_geometry': ['obs_general_id', 'phase1']},
        _REGISTRY,
    )
    do_validate.validate_nulls(_revertible(db))
    in_generation = _IN_GENERATION.replace('`g`', '`c`')
    assert db.selects == [
        (
            'SUM(`c`.`id` IS NULL), SUM(`c`.`time1` IS NULL) FROM `obs_general` `c` WHERE '
            + in_generation,
            [_SWITCHED, _SWITCHED],
        ),
        (
            'SUM(`c`.`obs_general_id` IS NULL), SUM(`c`.`phase1` IS NULL) FROM '
            '`obs_ring_geometry` `c` JOIN `obs_general` `g` ON `g`.`id` = `c`.`obs_general_id` '
            f'WHERE {_IN_GENERATION}',
            [_SWITCHED, _SWITCHED],
        ),
    ]


def test_the_null_check_counts_every_row_otherwise() -> None:
    """One scan of each table, with no condition and no value."""
    db = _ScopeDB({'obs_general': ['id', 'time1']}, _REGISTRY)
    do_validate.validate_nulls(_served(db))
    assert db.selects == [('SUM(`id` IS NULL), SUM(`time1` IS NULL) FROM `obs_general`', None)]


def test_unique_opus_ids_compare_the_generation_the_update_writes() -> None:
    """The pending generation's rows: its own and the served ones it keeps."""
    db = _ScopeDB(_TABLES, _REGISTRY)
    do_validate.validate_unique_opus_ids(_pending(db))
    (counted,) = db.selects
    assert '`g`.`added_generation` <= %s' in counted[0]
    assert counted[1] == [_PENDING, _PENDING]


def test_a_pending_validation_logs_its_scope_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """The generation, its observations and the first id are named before any check."""
    for name in dir(do_validate):
        if name.startswith('validate_'):
            monkeypatch.setattr(do_validate, name, lambda ctx: None)
    db = _ScopeDB(_TABLES | {'param_info__new': []}, _REGISTRY)
    db.count = 7
    ctx = _pending(db)
    monkeypatch.setattr(ctx.logger, 'close', lambda *args, **kwargs: (0, 0, 0, 0))
    assert do_validate.do_validate(ctx)
    assert ctx.logger.messages_at('info') == [
        f'Validating generation {_PENDING}: 7 observations, from obs_general id {_FIRST_ID}'
    ]
    assert db.selects == [
        (f'COUNT(*) FROM `obs_general` `g` WHERE {_ADDED}', [_FIRST_ID, _PENDING])
    ]
    db = _ScopeDB(_TABLES | {'param_info': []}, _REGISTRY)
    ctx = _served(db)
    monkeypatch.setattr(ctx.logger, 'close', lambda *args, **kwargs: (0, 0, 0, 0))
    assert do_validate.do_validate(ctx)
    assert ctx.logger.messages_at('info') == []
    assert db.selects == []
    db = _ScopeDB(_TABLES | {'param_info': []}, _REGISTRY)
    ctx = _revertible(db)
    monkeypatch.setattr(ctx.logger, 'close', lambda *args, **kwargs: (0, 0, 0, 0))
    assert do_validate.do_validate(ctx)
    assert ctx.logger.messages_at('info') == [
        f'Validating generation {_SWITCHED}, the one served, while the observations the last '
        'switch retired await "opus_import --purge-generations"'
    ]
    assert db.selects == []
