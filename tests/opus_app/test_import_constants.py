"""Tests for the per-process copies of the tables only an import changes.

`opus_app.apps.tools.import_constants`, the definitions in
`opus_app.apps.tools.dictionary` and the qualified-name and regular-expression caches in
`opus_app.apps.search.views` answer from memory what the views used to ask the database
on every request. The golden-response suite drives them through whole endpoints against
a real import; these tests stand fake managers in for the tables, so they run wherever
`pytest` does and count what reaches the database.

What is worth pinning, and why:

* **The server's comparison, not Python's.** The server compares labels without regard to
  case or accent, and callers rely on it (``planet=saturn`` finds ``Saturn``). A lookup
  that compared exactly would turn those requests into errors.
* **A label or a value names a row.** The query these replace matched either column, and
  a name matching two rows, or two names matching one row, changes the count the views
  check.
* **A miss asks the server.** Only the server's collation is authoritative, so a name not
  found in memory is looked up there rather than rejected.
* **Each table is read once.** That is the point of the module.
* **A refused regular expression is asked again.** The server refuses a pattern and a
  dropped connection the same way, so only acceptances are remembered.
"""

from collections.abc import Iterable, Iterator
from typing import Any

import pytest
from django.apps import apps
from django.db import DatabaseError
from django.db.models import Q

from opus_app.apps.paraminfo.models import ParamInfo
from opus_app.apps.search import views as search_views
from opus_app.apps.search.models import Partables, TableNames
from opus_app.apps.tools import dictionary, import_constants
from opus_app.apps.tools.dictionary import Definitions, get_def_for_tooltip, get_definition
from opus_app.apps.tools.import_constants import (
    MultTable,
    collation_key,
    displayed_table_names,
    get_table_name,
    mult_table,
    partables,
    table_names,
)

#: The rows of a fake mult table: id, value, label, disp_order.
PLANET_ROWS = [
    (0, None, 'N/A', '000'),
    (1, 'JUP', 'Jupiter', '010'),
    (2, 'SAT', 'Saturn', '020'),
    (3, 'URA', 'Uranus', '030'),
    # A label that is another row's value.
    (4, 'OTHER', 'SAT', '040'),
]


class FakeQuerySet:
    """Stands in for the queryset a fake mult table's `filter` returns."""

    def __init__(self, ids: list[int]) -> None:
        self.ids = ids

    def values_list(self, field: str, *, flat: bool) -> list[int]:
        """Return the matched ids, as `values_list('pk', flat=True)` would."""
        assert field == 'pk'
        assert flat
        return self.ids


class FakeMultManager:
    """Stands in for a mult model's manager, counting the queries it answers."""

    def __init__(self, rows: list[tuple[int, str | None, str, str]]) -> None:
        self.rows = rows
        self.queries = 0

    def values_list(self, *fields: str) -> list[tuple[int, str | None, str, str]]:
        """Return every row, as the loader asks for them."""
        assert fields == ('id', 'value', 'label', 'disp_order')
        self.queries += 1
        return self.rows

    def filter(self, condition: Q) -> FakeQuerySet:
        """Answer the server's lookup of a name, comparing exactly."""
        self.queries += 1
        names: set[str] = set()
        for child in condition.children:
            assert isinstance(child, tuple)
            names.update(child[1])
        ids = [row[0] for row in self.rows if row[1] in names or row[2] in names]
        return FakeQuerySet(ids)


class FakeMultModel:
    """Stands in for a mult model, holding only its manager."""

    def __init__(self, rows: list[tuple[int, str | None, str, str]]) -> None:
        self.objects = FakeMultManager(rows)


@pytest.fixture(autouse=True)
def _empty_caches() -> Iterator[None]:
    """Start and end every test with no cached copies."""

    def clear() -> None:
        table_names.cache_clear()
        import_constants.displayed_table_names.cache_clear()
        import_constants.table_names_collate_as_keys.cache_clear()
        import_constants._table_names_by_name.cache_clear()
        partables.cache_clear()
        mult_table.cache_clear()
        dictionary._definitions.cache_clear()
        search_views._PARAMINFO_BY_NAME_CACHE.clear()
        search_views._server_accepts_regex.cache_clear()

    clear()
    yield
    clear()


@pytest.fixture
def planet_model(monkeypatch: pytest.MonkeyPatch) -> FakeMultModel:
    """Make `obs_general.planet_id`'s mult table a fake with `PLANET_ROWS`."""
    model = FakeMultModel(PLANET_ROWS)

    def get_model(app_label: str, model_name: str) -> FakeMultModel:
        assert (app_label, model_name) == ('search', 'MultObsGeneralPlanetId')
        return model

    monkeypatch.setattr(apps, 'get_model', get_model)
    return model


# collation_key


@pytest.mark.parametrize(
    ('first', 'second'),
    [('Saturn', 'saturn'), ('Saturn', 'SATURN'), ('Jupiter', 'Jupitér'), ('Straße', 'STRASSE')],
    ids=['lower', 'upper', 'accent', 'sharp-s'],
)
def test__collation_key_ignores_case_and_accents(first: str, second: str) -> None:
    assert collation_key(first) == collation_key(second)


@pytest.mark.parametrize(
    ('first', 'second'),
    [('Saturn', 'Saturn '), ('Saturn', 'Saturns'), ('N/A', 'NA')],
    ids=['trailing-space', 'plural', 'punctuation'],
)
def test__collation_key_keeps_what_the_server_compares(first: str, second: str) -> None:
    assert collation_key(first) != collation_key(second)


# mult_table


def test__mult_table_reads_the_fields_table_once(planet_model: FakeMultModel) -> None:
    first = mult_table('obs_general.planet_id')
    second = mult_table('obs_general.planet_id')
    assert first is second
    assert planet_model.objects.queries == 1
    assert first.model_name == 'MultObsGeneralPlanetId'
    assert first.rows[2] == import_constants.MultRow(2, 'SAT', 'Saturn', '020')
    assert first.rows[0].value is None


@pytest.mark.parametrize(
    ('names', 'expected'),
    [
        (['Saturn'], [2]),
        (['saturn'], [2]),
        (['SATURN'], [2]),
        (['JUP'], [1]),
        (['jup', 'Uranus'], [1, 3]),
        (['Saturn', 'saturn'], [2]),
        (['SAT'], [2, 4]),
        (['N/A'], [0]),
        ([], []),
    ],
    ids=[
        'label',
        'label-lower',
        'label-upper',
        'value',
        'mixed',
        'two-names-one-row',
        'one-name-two-rows',
        'null-row',
        'none',
    ],
)
def test__ids_for_matches_labels_and_values_without_a_query(
    planet_model: FakeMultModel, names: list[str], expected: list[int]
) -> None:
    table = mult_table('obs_general.planet_id')
    assert table.ids_for(names) == expected
    assert planet_model.objects.queries == 1


def test__ids_for_asks_the_server_about_a_name_it_does_not_hold(
    planet_model: FakeMultModel,
) -> None:
    table = mult_table('obs_general.planet_id')
    assert table.ids_for(['Saturn', 'Pluto']) == [2]
    assert planet_model.objects.queries == 2


@pytest.mark.parametrize(
    'name',
    ['Sätürn', 'Sat\u00a8urn', 'Sat\x01urn'],
    ids=['accent', 'diaeresis-sign', 'control'],
)
def test__a_name_that_is_not_printable_ascii_asks_the_server(
    planet_model: FakeMultModel, name: str
) -> None:
    # The fake server compares exactly, so none of these matches there.
    table = mult_table('obs_general.planet_id')
    assert table.ids_for([name]) == []
    assert planet_model.objects.queries == 2


def test__ids_for_returns_what_the_server_matched_on_a_miss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A name the server's collation matches but this module's key does not: the
    # server's answer is the one returned.
    class Lenient(FakeMultManager):
        def filter(self, condition: Q) -> FakeQuerySet:
            self.queries += 1
            return FakeQuerySet([3, 1])

    model = FakeMultModel(PLANET_ROWS)
    model.objects = Lenient(PLANET_ROWS)
    monkeypatch.setattr(apps, 'get_model', lambda _app, _name: model)
    table = MultTable('MultObsGeneralPlanetId', {}, {}, ascii_only=True)
    assert table.ids_for(['anything']) == [1, 3]


def test__ids_for_accepts_any_iterable(planet_model: FakeMultModel) -> None:
    names: Iterable[str] = (name for name in ['Jupiter', 'Saturn'])
    assert mult_table('obs_general.planet_id').ids_for(names) == [1, 2]


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('Saturn', True),
        ('N/A', True),
        ('Sat urn', True),
        ('Sat\u00adurn', False),
        ('Sat\x01urn', False),
        ('Jupitér', False),
        ('General\u00a8Constraints', False),
    ],
    ids=['letters', 'punctuation', 'space', 'soft-hyphen', 'control', 'accent', 'diaeresis-sign'],
)
def test__only_printable_ascii_collates_as_its_key(text: str, expected: bool) -> None:
    assert import_constants.collates_as_key(text) is expected


def test__a_table_holding_a_control_character_asks_the_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = FakeMultModel([*PLANET_ROWS, (5, 'SAT2', 'Sat\x01urn', '050')])
    monkeypatch.setattr(apps, 'get_model', lambda _app, _name: model)
    table = mult_table('obs_general.planet_id')
    assert not table.ascii_only
    assert table.ids_for(['Saturn']) == [2]
    assert model.objects.queries == 2


def test__table_names_collate_as_keys_only_when_all_are_printable_ascii(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [_table_name('obs_general', 'General Constraints', 10)]
    monkeypatch.setattr(TableNames, 'objects', FakeRowManager(rows))
    assert import_constants.table_names_collate_as_keys()
    import_constants.table_names_collate_as_keys.cache_clear()
    table_names.cache_clear()
    displayed_table_names.cache_clear()
    rows.append(_table_name('obs_soft', 'Sat\u00adurn', 20))
    assert not import_constants.table_names_collate_as_keys()


def test__a_table_holding_a_name_that_is_not_ascii_asks_the_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The key does not ignore what the collation ignores, so a non-ASCII stored name
    # could be matched by the server and missed here.
    model = FakeMultModel([*PLANET_ROWS, (5, 'SAT\u00adURN', 'Sat\u00adurn', '050')])
    monkeypatch.setattr(apps, 'get_model', lambda _app, _name: model)
    table = mult_table('obs_general.planet_id')
    assert not table.ascii_only
    assert table.ids_for(['Jupiter']) == [1]
    assert model.objects.queries == 2


# table_names and partables


class FakeRowManager:
    """Stands in for the manager of `table_names` or `partables`."""

    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows
        self.queries = 0

    def order_by(self, field: str) -> list[Any]:
        """Return the rows sorted, as the loader asks for `table_names`."""
        assert field == 'disp_order'
        self.queries += 1
        return sorted(self.rows, key=lambda row: row.disp_order)

    def all(self) -> list[Any]:
        """Return the rows, as the loader asks for `partables`."""
        self.queries += 1
        return self.rows


def _table_name(table_name: str, label: str, disp_order: int) -> TableNames:
    return TableNames(table_name=table_name, label=label, display='Y', disp_order=disp_order)


def test__table_names_are_read_once_in_display_order(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = FakeRowManager(
        [
            _table_name('obs_pds', 'PDS Constraints', 20),
            _table_name('obs_general', 'General Constraints', 10),
        ]
    )
    monkeypatch.setattr(TableNames, 'objects', manager)
    assert [row.table_name for row in table_names()] == ['obs_general', 'obs_pds']
    assert get_table_name('obs_pds').label == 'PDS Constraints'
    assert get_table_name('obs_general').label == 'General Constraints'
    assert manager.queries == 1


def test__table_names_compare_as_the_server_does(monkeypatch: pytest.MonkeyPatch) -> None:
    hidden = _table_name('obs_hidden', 'Hidden', 30)
    hidden.display = 'N'
    lower = _table_name('obs_lower', 'Lower', 40)
    lower.display = 'y'
    manager = FakeRowManager([_table_name('obs_general', 'General Constraints', 10), hidden, lower])
    monkeypatch.setattr(TableNames, 'objects', manager)
    assert get_table_name('OBS_GENERAL').table_name == 'obs_general'
    assert [row.table_name for row in displayed_table_names()] == ['obs_general', 'obs_lower']


def test__get_table_name_raises_does_not_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(TableNames, 'objects', FakeRowManager([]))
    with pytest.raises(TableNames.DoesNotExist, match='obs_missing'):
        get_table_name('obs_missing')


def test__partables_are_read_once(monkeypatch: pytest.MonkeyPatch) -> None:
    row = Partables(
        trigger_tab='obs_general',
        trigger_col='instrument_id',
        trigger_val='COISS',
        partable='obs_mission_cassini',
    )
    manager = FakeRowManager([row])
    monkeypatch.setattr(Partables, 'objects', manager)
    assert partables() == (row,)
    assert partables() == (row,)
    assert manager.queries == 1


# definitions


class FakeDefinitionsManager:
    """Stands in for the manager of `definitions`."""

    def __init__(self, rows: list[tuple[str, str, str]]) -> None:
        self.rows = rows
        self.queries = 0

    def values_list(self, *fields: str) -> list[tuple[str, str, str]]:
        """Return every row, as the loader asks for them."""
        assert fields == ('context', 'term', 'definition')
        self.queries += 1
        return self.rows


@pytest.fixture
def definitions(monkeypatch: pytest.MonkeyPatch) -> FakeDefinitionsManager:
    """Make `definitions` a fake with two rows."""
    manager = FakeDefinitionsManager(
        [
            ('OPUS_PRODUCT_TYPE', 'coiss_raw', 'Raw image'),
            ('OPUS_GENERAL', 'time1', 'Start time'),
        ]
    )
    monkeypatch.setattr(Definitions, 'objects', manager)
    return manager


def test__definitions_are_read_once(definitions: FakeDefinitionsManager) -> None:
    assert get_definition('coiss_raw', 'OPUS_PRODUCT_TYPE') == 'Raw image'
    assert get_definition('time1', 'OPUS_GENERAL') == 'Start time'
    assert definitions.queries == 1


def test__definitions_compare_as_the_server_does(definitions: FakeDefinitionsManager) -> None:
    assert get_definition('COISS_RAW', 'opus_product_type') == 'Raw image'


@pytest.mark.parametrize(
    ('term', 'context'),
    [
        ('coiss_raw', 'OPUS_GENERAL'),
        ('nothing', 'OPUS_GENERAL'),
        (None, 'OPUS_GENERAL'),
        ('time1', None),
    ],
    ids=['other-context', 'unknown-term', 'no-term', 'no-context'],
)
def test__an_undefined_term_has_no_definition(
    definitions: FakeDefinitionsManager, term: str | None, context: str | None
) -> None:
    assert get_definition(term, context) is None


def test__a_missing_mult_tooltip_is_not_an_error(
    definitions: FakeDefinitionsManager, caplog: pytest.LogCaptureFixture
) -> None:
    assert get_def_for_tooltip('JUP', 'MULT_OBS_GENERAL_PLANET_ID') is None
    assert caplog.records == []


# The qualified-name cache


class FakeParamInfoManager:
    """Stands in for `ParamInfo.objects`, answering `get` from a set of columns."""

    def __init__(self, columns: set[tuple[str, str]]) -> None:
        self.columns = columns
        self.queries = 0

    def get(self, *, category_name: str, name: str) -> ParamInfo:
        """Return a row for a known column and raise for any other."""
        self.queries += 1
        if (category_name, name) not in self.columns:
            raise ParamInfo.DoesNotExist
        return ParamInfo(category_name=category_name, name=name)


@pytest.fixture
def param_info(monkeypatch: pytest.MonkeyPatch) -> FakeParamInfoManager:
    """Make `param_info` a fake with a two-column range and a single-column one."""
    manager = FakeParamInfoManager(
        {
            ('obs_general', 'time1'),
            ('obs_general', 'time2'),
            ('obs_general', 'observation_duration'),
        }
    )
    monkeypatch.setattr(ParamInfo, 'objects', manager)
    return manager


def test__a_qualified_name_is_looked_up_once(param_info: FakeParamInfoManager) -> None:
    first = search_views._get_param_info_by_qualified_name('obs_general.time1')
    second = search_views._get_param_info_by_qualified_name('obs_general.time1')
    assert first is not None
    assert second is not None
    assert (first.category_name, first.name) == ('obs_general', 'time1')
    assert first is not second
    assert param_info.queries == 1


def test__a_single_column_range_is_found_without_its_suffix(
    param_info: FakeParamInfoManager,
) -> None:
    pi = search_views._get_param_info_by_qualified_name('obs_general.observation_duration1')
    assert pi is not None
    assert pi.name == 'observation_duration'
    assert search_views.is_single_column_range('obs_general.observation_duration1')
    assert not search_views.is_single_column_range('obs_general.time1')
    # observation_duration1, observation_duration, time; each once.
    assert param_info.queries == 3


def test__an_unknown_qualified_name_is_cached_as_none(param_info: FakeParamInfoManager) -> None:
    assert search_views._get_param_info_by_qualified_name('obs_general.nothing') is None
    assert search_views._get_param_info_by_qualified_name('obs_general.nothing') is None
    assert search_views._get_param_info_by_qualified_name('nothing') is None
    assert param_info.queries == 1


# The regular-expression check


class FakeCursor:
    """Stands in for a cursor, refusing every pattern with an unclosed bracket."""

    def __init__(self, executed: list[str]) -> None:
        self.executed = executed

    def execute(self, sql: str, params: tuple[str]) -> None:
        """Record the pattern and refuse it the way the server would."""
        self.executed.append(params[0])
        if params[0].count('(') != params[0].count(')'):
            raise DatabaseError('Mismatched parenthesis in regular expression.')


class FakeConnection:
    """Stands in for `django.db.connection`, recording the patterns it is asked about."""

    def __init__(self) -> None:
        self.executed: list[str] = []

    def cursor(self) -> FakeCursor:
        """Return a cursor that records into this connection."""
        return FakeCursor(self.executed)


def test__an_accepted_regex_is_asked_once_and_a_refused_one_every_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeConnection()
    monkeypatch.setattr(search_views, 'connection', fake)
    assert search_views._valid_regex('^N(1|2)')
    assert search_views._valid_regex('^N(1|2)')
    assert not search_views._valid_regex('^N(1')
    assert not search_views._valid_regex('^N(1')
    assert fake.executed == ['^N(1|2)', '^N(1', '^N(1']


# The slug cache, for a search slug that carries its range suffix


class FakeSlugManager:
    """Stands in for `ParamInfo.objects`, answering `get` by slug."""

    def __init__(self) -> None:
        self.queries = 0

    def get(self, *, slug: str) -> ParamInfo:
        """Return a two-column range's first column for its own slug."""
        self.queries += 1
        if slug != 'time1':
            raise ParamInfo.DoesNotExist
        return ParamInfo(category_name='obs_general', name='time1', slug='time1')


def test__a_suffixed_search_slug_is_looked_up_once(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = FakeSlugManager()
    monkeypatch.setattr(ParamInfo, 'objects', manager)
    monkeypatch.setattr(search_views, '_PARAMINFO_CACHE', {})
    first = search_views.get_param_info_by_slug('time1', 'search')
    second = search_views.get_param_info_by_slug('time1', 'search')
    assert first is not None
    assert second is not None
    assert first is not second
    assert manager.queries == 1
