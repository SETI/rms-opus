"""The option prototypes: the columns and statements they are built from, and the builds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from benchmarks import option_prototypes
from benchmarks.option_prototypes import FacetColumn, PrototypeError
from opus_import import generations, import_util
from opus_import.importdb import mysql


def test_the_facet_table_holds_every_single_valued_mult_field_of_a_one_row_table() -> None:
    """Each column is a mult id, a yes/no or an on/off flag, of obs_general or of a table
    keyed by its observation alone, named by its field's qualified name."""
    columns = option_prototypes.facet_columns()
    names = [column.name for column in columns]
    assert 'obs_general.instrument_id' in names
    assert 'obs_type_image.image_type_id' in names
    assert 'obs_mission_hubble.pc1_flag' in names
    assert 'obs_instrument_cocirs.instrument_mode_all_flag' in names
    assert names == sorted(names)
    assert {column.sql_type for column in columns} == {'smallint unsigned'}
    assert all(column.name == f'{column.table}.{column.column}' for column in columns)
    assert all(option_prototypes.is_observation_table(column.table) for column in columns)


@pytest.mark.parametrize(
    'name',
    [
        'obs_general.target_name',
        'obs_general.target_class',
        'obs_general_target_name.mult_id',
        'obs_surface_geometry_name.target_name',
    ],
    ids=['list-column', 'list-column-class', 'junction', 'several-rows-per-observation'],
)
def test_the_facet_table_holds_no_list_and_no_field_of_a_table_of_several_rows(name: str) -> None:
    """A list column, its junction table and a surface geometry field have no facet column."""
    assert name not in {column.name for column in option_prototypes.facet_columns()}


@pytest.mark.parametrize(
    ('table', 'expected'),
    [
        ('obs_general', True),
        ('obs_type_image', True),
        ('obs_instrument_coiss', True),
        ('obs_surface_geometry_target', False),
        ('obs_files', False),
    ],
)
def test_a_table_holds_one_row_per_observation_when_its_key_is_the_observation(
    table: str, expected: bool
) -> None:
    """obs_general, and a table whose primary key is obs_general_id alone."""
    assert option_prototypes.is_observation_table(table) is expected


_COLUMNS = [
    FacetColumn('obs_general.planet_id', 'obs_general', 'planet_id', 'smallint unsigned'),
    FacetColumn('obs_wavelength.spec_flag', 'obs_wavelength', 'spec_flag', 'smallint unsigned'),
    FacetColumn(
        'obs_type_image.image_type_id', 'obs_type_image', 'image_type_id', 'smallint unsigned'
    ),
]


def test_the_facet_table_is_keyed_by_the_observation() -> None:
    """The key, then one column per field, named by qualified name."""
    assert option_prototypes.facet_table_sql(_COLUMNS) == (
        'CREATE TABLE `obs_facet` (`obs_general_id` INT UNSIGNED NOT NULL PRIMARY KEY, '
        '`obs_general.planet_id` SMALLINT UNSIGNED, `obs_wavelength.spec_flag` SMALLINT UNSIGNED, '
        '`obs_type_image.image_type_id` SMALLINT UNSIGNED) ENGINE=InnoDB '
        f'STATS_SAMPLE_PAGES={mysql.STATS_SAMPLE_PAGES}'
    )


def test_the_facet_table_is_filled_by_one_statement_joining_the_hub_and_the_children() -> None:
    """Every observation obs_general shows, each child left joined once by observation."""
    assert option_prototypes.facet_fill_sql(_COLUMNS) == (
        'INSERT INTO `obs_facet` (`obs_general_id`, `obs_general.planet_id`, '
        '`obs_wavelength.spec_flag`, `obs_type_image.image_type_id`) SELECT `obs_general`.`id`, '
        '`obs_general`.`planet_id`, `obs_wavelength`.`spec_flag`, `obs_type_image`.`image_type_id` '
        'FROM `obs_general` LEFT JOIN `obs_type_image` ON `obs_type_image`.`obs_general_id` = '
        '`obs_general`.`id` LEFT JOIN `obs_wavelength` ON `obs_wavelength`.`obs_general_id` = '
        '`obs_general`.`id`'
    )


def test_the_rank_is_a_keyed_column_numbered_in_the_default_order() -> None:
    """The column and its key in one ALTER, then each row's ROW_NUMBER over time1, opus_id."""
    assert option_prototypes.rank_alter_sql('obs_general_rows') == (
        'ALTER TABLE `obs_general_rows` ADD COLUMN `default_rank` INT UNSIGNED, '
        'ADD KEY `default_rank` (`default_rank`)'
    )
    assert option_prototypes.rank_fill_sql('obs_general_rows') == (
        'UPDATE `obs_general_rows` AS `ranked_row` JOIN (SELECT `id`, ROW_NUMBER() OVER '
        '(ORDER BY `time1`, `opus_id`) AS `rank_value` FROM `obs_general_rows`) AS `ranking` '
        'ON `ranking`.`id` = `ranked_row`.`id` SET `ranked_row`.`default_rank` = '
        '`ranking`.`rank_value`'
    )


def test_the_view_is_given_obs_general_json_and_the_rank_after_it() -> None:
    """The import's view code lists the rank last, after obs_general.json's columns."""
    schema = option_prototypes.view_schema_with_rank()
    packaged = json.loads(
        (import_util.TABLE_SCHEMA_DIR / 'obs_general.json').read_text(encoding='utf-8')
    )
    assert schema[:-1] == packaged
    assert generations.view_columns(schema)[-1] == 'default_rank'
    assert generations.view_columns(schema)[:-1] == generations.view_columns(packaged)


class _ImportDB:
    """The import's database connection, recording the view it is asked for."""

    def __init__(self, made: list[dict[str, Any]], *args: Any, **kwargs: Any) -> None:
        """Record how it was opened, in the list given."""
        self.entry: dict[str, Any] = {'args': args, 'kwargs': kwargs, 'closed': False}
        made.append(self.entry)

    def create_obs_general_view(self, schema: list[dict[str, Any]]) -> None:
        """Record the schema the view lists."""
        self.entry['view'] = schema

    def close(self) -> None:
        """Record the close."""
        self.entry['closed'] = True


def test_the_view_is_made_by_the_imports_own_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """The copy's view is created by ImportDBMySQL, with no bulk load, then closed."""
    made: list[dict[str, Any]] = []
    monkeypatch.setattr(
        option_prototypes, 'ImportDBMySQL', lambda *args, **kwargs: _ImportDB(made, *args, **kwargs)
    )
    option_prototypes.recreate_view('copy')
    (entry,) = made
    assert entry['args'][2] == 'copy'
    assert entry['kwargs'] == {'bulk_load': False}
    assert entry['view'] == option_prototypes.view_schema_with_rank()
    assert entry['closed'] is True


class _Copy:
    """A connection to a copy, answering the builds' statements and recording them."""

    def __init__(
        self,
        *,
        rows_table: bool = True,
        rank_present: bool = False,
        tables: tuple[str, ...] = ('obs_general', 'obs_wavelength', 'obs_type_image'),
        view_columns: list[str] | None = None,
        version_row: tuple[Any, Any] | None = (None, 0),
        view_definition: str | None = 'select `id` AS `id` from `obs_general_rows`',
    ) -> None:
        """Hold the copy's shape: whether obs_general is a view of obs_general_rows, whether
        the rank exists, its tables, the columns its view lists (obs_general.json's by
        default), its version row's pending generation and revertible flag (None for no
        such columns), and its view's definition (None for no view)."""
        self.rows_table = rows_table
        self.rank_present = rank_present
        self.tables = tables
        packaged = generations.view_columns(option_prototypes.view_schema_with_rank()[:-1])
        self.view_columns = packaged if view_columns is None else view_columns
        self.version_row = version_row
        self.view_definition = view_definition
        self.executed: list[str] = []
        self.sizes = iter([(1000, 200), (1100, 400), (5000, 0)])
        self._answer: list[tuple[Any, ...]] = []

    def cursor(self) -> _Copy:
        """Return itself as the cursor."""
        return self

    def close(self) -> None:
        """Close nothing."""

    def execute(self, statement: str, parameters: Any) -> None:
        """Answer each statement a build issues."""
        self.executed.append(statement)
        answers: list[tuple[str, list[tuple[Any, ...]]]] = [
            ('SELECT COUNT(*) FROM information_schema.TABLES', [(1 if self.rows_table else 0,)]),
            ('SELECT COUNT(*) FROM information_schema.COLUMNS', [(1 if self.rank_present else 0,)]),
            (
                'SELECT VIEW_DEFINITION',
                [] if self.view_definition is None else [(self.view_definition,)],
            ),
            ('SELECT `pending_generation`', [] if self.version_row is None else [self.version_row]),
            ('SELECT @@GLOBAL.innodb_fast_shutdown', [(1,)]),
            ('SELECT TABLE_NAME FROM', [(table,) for table in self.tables]),
            ('SELECT stat_value', [(16384,)]),
            ('SELECT COUNT(`default_rank`)', [(399,)]),
            ('SELECT COUNT(*) FROM `obs_facet`', [(399,)]),
        ]
        if statement.startswith('SELECT DATA_LENGTH'):
            self._answer = [next(self.sizes)]
            return
        if statement.startswith('SELECT COLUMN_NAME FROM information_schema.COLUMNS'):
            if 'ORDER BY ORDINAL_POSITION' in statement:
                self._answer = [(name,) for name in self.view_columns]
            elif self.version_row is None:
                self._answer = []
            else:
                self._answer = [('version',), ('pending_generation',), ('revertible',)]
            return
        self._answer = next((rows for start, rows in answers if statement.startswith(start)), [])

    def fetchall(self) -> list[tuple[Any, ...]]:
        """Return the last statement's rows."""
        return self._answer


def test_the_rank_prototype_alters_fills_and_remakes_the_view_and_reads_its_cost() -> None:
    """The ALTER, then the fill, then the view; the bytes are the base table's change and
    the key's own size."""
    copy = _Copy()
    views: list[str] = []
    metrics, details = option_prototypes.build_default_rank(copy, 'copy', make_view=views.append)
    writes = [text for text in copy.executed if text.startswith(('ALTER', 'UPDATE'))]
    assert writes == [details['statements']['alter'], details['statements']['fill']]
    assert views == ['copy']
    assert metrics['prototype.default_rank.data_bytes'] == 100
    assert metrics['prototype.default_rank.index_bytes'] == 200
    assert metrics['prototype.default_rank.key_bytes'] == 16384
    assert metrics['prototype.default_rank.rows'] == 399
    assert metrics['prototype.default_rank.build_s'] == pytest.approx(
        metrics['prototype.default_rank.alter_s']
        + metrics['prototype.default_rank.fill_s']
        + metrics['prototype.default_rank.view_s']
    )
    assert details['base_table'] == 'obs_general_rows'
    assert (
        sum(text.startswith('ANALYZE TABLE `copy`.`obs_general_rows`') for text in copy.executed)
        == 2
    )


def test_a_schema_whose_obs_general_is_a_table_is_ranked_without_a_view() -> None:
    """Where obs_general is the base table, the rank goes there and no view is made."""
    copy = _Copy(rows_table=False)
    views: list[str] = []
    metrics, details = option_prototypes.build_default_rank(copy, 'copy', make_view=views.append)
    assert views == []
    assert metrics['prototype.default_rank.view_s'] == 0.0
    assert details['statements']['alter'].startswith('ALTER TABLE `obs_general` ADD')


@pytest.mark.parametrize(
    ('copy', 'message'),
    [
        (_Copy(version_row=(2, 0)), r'pending generation \(2\)'),
        (_Copy(version_row=(None, 1)), r'revertible switch \(True\)'),
        (
            _Copy(
                view_definition='select `id` AS `id` from `obs_general_rows` where '
                '(`obs_general_rows`.`added_generation` <= 1)'
            ),
            'is a view with a condition',
        ),
        (
            _Copy(view_definition='select `id` AS `id` from `obs_general_rows` limit 10'),
            'or a row limit',
        ),
    ],
    ids=['pending-generation', 'revertible-switch', 'view-condition', 'view-limit'],
)
def test_a_source_that_may_hide_rows_is_refused(copy: _Copy, message: str) -> None:
    """A pending generation (even one with no rows yet), a revertible switch, or a view
    with a condition or a row limit: the rank's view, made again, would drop what it
    hides."""
    with pytest.raises(PrototypeError, match=message):
        option_prototypes.require_served_view(copy, 'full')


@pytest.mark.parametrize(
    'copy',
    [
        _Copy(),
        _Copy(version_row=None, view_definition=None),
        _Copy(view_definition="select 'where' AS `w`, `id` AS `id` from `obs_general_rows`"),
        _Copy(view_definition="select 'limit' AS `l`, `id` AS `id` from `obs_general_rows`"),
    ],
    ids=['served', 'no-generations', 'where-in-a-literal', 'limit-in-a-literal'],
)
def test_a_source_serving_every_row_is_accepted(copy: _Copy) -> None:
    """No pending generation, no revertible switch, and no condition outside quotes."""
    option_prototypes.require_served_view(copy, 'full')


def test_a_copy_whose_view_lists_other_columns_is_refused() -> None:
    """The view made again would silently differ from the one copied."""
    copy = _Copy(view_columns=['id', 'opus_id'])
    with pytest.raises(PrototypeError, match=r'lists other columns than obs_general\.json'):
        option_prototypes.build_default_rank(copy, 'copy', make_view=print)
    assert not any(text.startswith('ALTER') for text in copy.executed)


def test_a_copy_already_ranked_is_refused() -> None:
    """The ALTER would fail half-way; the refusal comes first and says why."""
    with pytest.raises(PrototypeError, match='already has the column default_rank'):
        option_prototypes.build_default_rank(_Copy(rank_present=True), 'copy', make_view=print)


def test_the_facet_prototype_creates_and_fills_the_table_and_reads_its_cost() -> None:
    """The table is created and filled once, its bytes read after; a field whose table the
    copy lacks is left out and named."""
    copy = _Copy(tables=('obs_general', 'obs_type_image'))
    metrics, details = option_prototypes.build_facet(copy, 'copy')
    writes = [text for text in copy.executed if text.startswith(('CREATE', 'INSERT'))]
    assert writes == [details['statements']['create'], details['statements']['fill']]
    built = {name for name, _table, _column in details['columns']}
    assert 'obs_type_image.image_type_id' in built
    assert 'obs_wavelength.spec_flag' not in built
    assert ['obs_wavelength.spec_flag', 'obs_wavelength', 'spec_flag'] in details['left_out']
    assert metrics['prototype.facet.columns'] == len(details['columns'])
    assert metrics['prototype.facet.data_bytes'] == 1000
    assert metrics['prototype.facet.index_bytes'] == 200
    assert metrics['prototype.facet.rows'] == 399


def test_a_copy_that_already_has_the_facet_table_is_refused() -> None:
    """Creating it again would fail; the refusal says why."""
    with pytest.raises(PrototypeError, match='already has the table obs_facet'):
        option_prototypes.build_facet(_Copy(tables=('obs_general', 'obs_facet')), 'copy')


class _Server:
    """The owned server, as the prototype command uses it."""

    def __init__(self, copy: _Copy) -> None:
        """Hold the copy every connection reaches."""
        self.copy = copy
        self.schemas: list[str | None] = []

    def connect(self, schema: str | None = None) -> _Copy:
        """Return the copy's connection."""
        self.schemas.append(schema)
        return self.copy

    def restart(self) -> None:
        """Note the restart among the copy's statements."""
        self.copy.executed.append('restart')


def _build(
    monkeypatch: pytest.MonkeyPatch, option: str, copy: _Copy | None = None
) -> tuple[dict[str, Any], _Server, list[tuple[Any, ...]]]:
    """Build one option with the clone stood in for; return the run, server and clones."""
    cloned: list[tuple[Any, ...]] = []

    def clone(
        _server: Any, source: str, target: str, *, version: int | None, defer_keys: bool
    ) -> float:
        cloned.append((source, target, version, defer_keys))
        return 2.5

    monkeypatch.setattr(option_prototypes, 'clone_schema', clone)
    server = _Server(_Copy() if copy is None else copy)
    run = option_prototypes.build_prototype(
        server,  # type: ignore[arg-type]
        source='full',
        target='copy',
        option=option,
        version=13,
        make_view=print,
    )
    return run, server, cloned


def test_a_prototype_is_built_on_a_copy_laid_out_as_the_import_lays_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The source is checked, then cloned with its keys built after its rows, with the
    version given, and the build runs on the target, whose name the run keeps."""
    run, server, cloned = _build(monkeypatch, 'facet')
    assert cloned == [('full', 'copy', 13, True)]
    assert server.schemas[:2] == [None, 'copy']
    assert server.copy.executed[0].startswith('SELECT COLUMN_NAME FROM information_schema.COLUMNS')
    assert run['kind'] == 'prototype'
    assert run['metrics']['prototype.facet.clone_s'] == 2.5
    assert run['details']['source'] == 'full'
    assert run['details']['schema'] == 'copy'
    assert 'SET SESSION information_schema_stats_expiry = 0' in server.copy.executed


def test_a_built_copy_is_settled_by_one_slow_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    """After the build, the server restarts with innodb_fast_shutdown 0, which is then put
    back as it was."""
    run, server, _cloned = _build(monkeypatch, 'facet')
    executed = server.copy.executed
    restart = executed.index('restart')
    assert executed[restart - 1] == 'SET GLOBAL innodb_fast_shutdown = 0'
    assert executed[restart + 1] == 'SET GLOBAL innodb_fast_shutdown = %s'
    assert max(i for i, text in enumerate(executed) if text.startswith('INSERT')) < restart
    assert 'prototype.facet.settle_s' in run['metrics']


def test_the_bare_copy_adds_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """The none option is the copy alone, settled like the others."""
    run, server, cloned = _build(monkeypatch, 'none')
    assert cloned == [('full', 'copy', 13, True)]
    assert not any(
        text.startswith(('ALTER', 'UPDATE', 'CREATE', 'INSERT')) for text in server.copy.executed
    )
    assert sorted(run['metrics']) == ['prototype.none.clone_s', 'prototype.none.settle_s']
    assert run['details']['option'] == 'none'


def test_a_source_that_may_hide_rows_is_refused_before_it_is_copied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The refusal comes before the clone, which would otherwise copy the whole schema."""
    with pytest.raises(PrototypeError, match='pending generation'):
        _build(monkeypatch, 'facet', _Copy(version_row=(2, 0)))


@pytest.mark.parametrize(
    ('source', 'target', 'option', 'message'),
    [
        ('full', 'full', 'facet', 'cannot be the source'),
        ('full', 'copy', 'other', 'unknown option'),
    ],
    ids=['copy-is-source', 'unknown-option'],
)
def test_a_prototype_that_would_touch_the_source_or_is_unknown_is_refused(
    source: str, target: str, option: str, message: str
) -> None:
    """The source is never the copy, and only the two options are built."""
    with pytest.raises(PrototypeError, match=message):
        option_prototypes.build_prototype(
            _Server(_Copy()),  # type: ignore[arg-type]
            source=source,
            target=target,
            option=option,
            version=None,
        )


def test_the_command_refuses_another_checkout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The prototypes are built by this checkout's import code, so only it is the side."""
    monkeypatch.delenv('PYTHONPATH', raising=False)
    arguments = ['--scale', 'fixture', '--side', 'after', '--pr', 'PR-nn', '--session', 'a']
    arguments += ['--python', 'python', '--repo-root', str(tmp_path)]
    arguments += ['--source', 'full', '--target', 'copy', '--option', 'facet']
    with pytest.raises(SystemExit, match='built with this checkout'):
        option_prototypes.main(arguments)
