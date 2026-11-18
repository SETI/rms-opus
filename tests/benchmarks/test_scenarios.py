"""The scenario files, their loaders, and their agreement with the sequences they copy."""

from pathlib import Path

import pytest

from benchmarks import import_scenarios, opus_config_file, web_scenarios
from benchmarks.app_servers import ServerError
from benchmarks.web_scenarios import ScenarioError
from import_tests.tools import holdings_survey
from opus_config import load_config
from opus_import import import_all

REPO_ROOT = Path(__file__).resolve().parents[2]
IMPORT_FOR_TESTS = REPO_ROOT / 'scripts' / 'import' / 'import_for_tests.sh'


def test_the_test_scale_groups_are_import_for_tests_sh_s(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same bundles, in the same order, as the script the API goldens come from, with no
    options of their own, as it gives none."""
    monkeypatch.setenv('PDS_DROPBOX_ROOT', '/holdings-root')
    scenario = import_scenarios.load_scenario('test')
    bundles = [bundle for group in scenario.groups for bundle in group.bundles.split(',')]
    assert bundles == holdings_survey.script_bundle_descriptors(IMPORT_FOR_TESTS)
    assert [group.options for group in scenario.groups] == [()] * len(scenario.groups)


def test_the_complete_scale_groups_are_opus_import_all_s(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same bundle sets, in the order the full-holdings import registers them, with no
    options of their own, as it gives none."""
    monkeypatch.setenv('PDS_DROPBOX_ROOT', '/holdings-root')
    scenario = import_scenarios.load_scenario('complete')
    expected = [(name, ()) for name in import_all.BUNDLE_SETS]
    assert [(group.bundles, group.options) for group in scenario.groups] == expected


def test_the_largest_bundle_is_one_the_test_scale_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    """The bundle imported alone and appended is one of the scale's own bundles."""
    monkeypatch.setenv('PDS_DROPBOX_ROOT', '/holdings-root')
    scenario = import_scenarios.load_scenario('test')
    named = {bundle for group in scenario.groups for bundle in group.bundles.split(',')}
    assert scenario.largest in named


def test_holdings_paths_expand_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The scenario names no machine's layout; the environment supplies it."""
    monkeypatch.setenv('PDS_DROPBOX_ROOT', '/holdings-root')
    scenario = import_scenarios.load_scenario('test')
    assert scenario.pds3_holdings == Path('/holdings-root/holdings')


def test_an_unset_holdings_variable_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unexpanded variable would otherwise become a directory name."""
    monkeypatch.delenv('PDS_DROPBOX_ROOT', raising=False)
    with pytest.raises(ServerError, match='names an environment variable that is not set'):
        import_scenarios.load_scenario('test')


def test_the_fixture_scenario_names_no_groups() -> None:
    """The fixture's bundles come from build_run, so its file lists none."""
    scenario = import_scenarios.load_scenario('fixture')
    assert scenario.groups == ()


def test_web_toml_expands_into_uniquely_named_scenarios() -> None:
    """Every scenario has requests, and no two share a name."""
    config = web_scenarios.load_web_config()
    names = [scenario.name for scenario in config.scenarios]
    assert len(names) == len(set(names))
    assert all(len(scenario.requests) > 0 for scenario in config.scenarios)


def test_the_concurrency_fanout_carries_its_search() -> None:
    """Every fan-out request of the concurrency scenario names the user's search."""
    concurrency = web_scenarios.load_web_config().concurrency
    assert concurrency is not None
    assert all('{search}' in request.url for request in concurrency.fanout)


def test_the_concurrency_searches_are_all_new() -> None:
    """No user's own search is another's, nor the shared one, so every one is built."""
    concurrency = web_scenarios.load_web_config().concurrency
    assert concurrency is not None
    distinct = [concurrency.distinct.format(i=i) for i in range(concurrency.users)]
    assert len(set(distinct)) == concurrency.users
    assert concurrency.shared not in distinct


@pytest.mark.parametrize('scale', ['fixture', 'test', 'complete'])
def test_every_scale_has_a_web_run_count(scale: str) -> None:
    """A scale without a count would make bench_web fail at the start of a session."""
    assert web_scenarios.load_web_config().runs[scale] > 0


def test_a_pages_scenario_builds_untimed_and_completes_its_last_page(tmp_path: Path) -> None:
    """The result count is untimed, and the last page waits for the count."""
    path = tmp_path / 'web.toml'
    path.write_text(
        '[server]\nport = 1\nworkers = 1\nthreads = 1\nmemcached_port = 2\nmemcached_mb = 1\n'
        '[runs]\nfixture = 1\n[searches]\nbroad = "time1=2000-01-01"\n'
        '[[scenarios]]\nkind = "pages"\nsearch = "broad"\n'
    )
    scenario = web_scenarios.load_web_config(path).scenarios[0]
    assert [(request.name, request.timed) for request in scenario.requests] == [
        ('build', False),
        ('page_1', True),
        ('page_10', True),
        ('page_last', True),
    ]
    assert scenario.requests[3].url == 'api/data.json?time1=2000-01-01&page={last}&limit=100'
    assert scenario.last_page_of == 'broad'


def test_a_pages_scenario_asks_for_its_column_set(tmp_path: Path) -> None:
    """A column set replaces the default columns on every page, and names the scenario."""
    path = tmp_path / 'web.toml'
    path.write_text(
        '[server]\nport = 1\nworkers = 1\nthreads = 1\nmemcached_port = 2\nmemcached_mb = 1\n'
        '[runs]\nfixture = 1\n[searches]\nbroad = "time1=2000-01-01"\n'
        '[columns]\nwide = "opusid,RINGGEOringradius1"\n'
        '[[scenarios]]\nkind = "pages"\nsearch = "broad"\n'
        '[[scenarios]]\nkind = "pages"\nsearch = "broad"\ncolumns = "wide"\n'
    )
    plain, wide = web_scenarios.load_web_config(path).scenarios
    assert plain.name == 'pages.broad'
    assert wide.name == 'pages.broad_wide'
    assert wide.last_page_of == 'broad'
    assert wide.requests[0].url == plain.requests[0].url
    assert [request.url for request in wide.requests[1:]] == [
        'api/data.json?time1=2000-01-01&cols=opusid,RINGGEOringradius1&page=1&limit=100',
        'api/data.json?time1=2000-01-01&cols=opusid,RINGGEOringradius1&page=10&limit=100',
        'api/data.json?time1=2000-01-01&cols=opusid,RINGGEOringradius1&page={last}&limit=100',
    ]


@pytest.mark.parametrize(
    ('entry', 'message'),
    [
        ('kind = "pages"\nsearch = "broad"\ncolumns = "none"\n', 'unknown columns'),
        ('kind = "search"\nsearch = "broad"\ncolumns = "wide"\n', 'only a pages scenario'),
    ],
)
def test_a_column_set_that_cannot_be_asked_for_is_refused(
    tmp_path: Path, entry: str, message: str
) -> None:
    """An unknown column set, or one on a scenario that pages nothing, fails at load."""
    path = tmp_path / 'web.toml'
    path.write_text(
        '[server]\nport = 1\nworkers = 1\nthreads = 1\nmemcached_port = 2\nmemcached_mb = 1\n'
        '[runs]\nfixture = 1\n[searches]\nbroad = "time1=2000-01-01"\n'
        '[columns]\nwide = "opusid"\n'
        f'[[scenarios]]\n{entry}'
    )
    with pytest.raises(web_scenarios.ScenarioError, match=message):
        web_scenarios.load_web_config(path)


def test_a_mults_scenario_builds_untimed_then_counts_the_default_widgets_and_its_own(
    tmp_path: Path,
) -> None:
    """The result count is untimed; the default widgets' counts come first, then
    [mults] widgets'."""
    path = tmp_path / 'web.toml'
    path.write_text(
        '[server]\nport = 1\nworkers = 1\nthreads = 1\nmemcached_port = 2\nmemcached_mb = 1\n'
        '[runs]\nfixture = 1\n[searches]\nbroad = "time1=2000-01-01"\n'
        '[fanout]\nmult_widgets = ["instrument"]\nrange_slugs = []\n'
        '[mults]\nwidgets = ["imagetype"]\n'
        '[[scenarios]]\nkind = "mults"\nsearch = "broad"\n'
    )
    scenario = web_scenarios.load_web_config(path).scenarios[0]
    assert scenario.name == 'mults.broad'
    assert [(request.name, request.timed) for request in scenario.requests] == [
        ('build', False),
        ('mults_instrument', True),
        ('mults_imagetype', True),
    ]
    assert [request.url for request in scenario.requests] == [
        '__api/meta/result_count.json?time1=2000-01-01&reqno=1',
        '__api/meta/mults/instrument.json?time1=2000-01-01&reqno=1',
        '__api/meta/mults/imagetype.json?time1=2000-01-01&reqno=1',
    ]


def test_an_unknown_search_is_refused(tmp_path: Path) -> None:
    """A scenario naming a search web.toml does not define fails at load."""
    path = tmp_path / 'web.toml'
    path.write_text(
        '[server]\nport = 1\nworkers = 1\nthreads = 1\nmemcached_port = 2\nmemcached_mb = 1\n'
        '[runs]\nfixture = 1\n[searches]\nempty = ""\n'
        '[[scenarios]]\nkind = "search"\nsearch = "missing"\n'
    )
    with pytest.raises(ScenarioError, match="unknown search 'missing'"):
        web_scenarios.load_web_config(path)


_SERVER = (
    '[server]\nport = 1\nworkers = 1\nthreads = 1\nmemcached_port = 2\nmemcached_mb = 1\n'
    '[runs]\nfixture = 1\n[searches]\nempty = ""\n'
)


@pytest.mark.parametrize(
    ('scenarios', 'message'),
    [
        ('[[scenarios]]\nkind = "pages"\n', 'names no search'),
        ('[[scenarios]]\nkind = "categories"\n', r'needs this scale\'s \[observations\]'),
        (
            '[[scenarios]]\nkind = "autocomplete"\nslug = "bundleid"\nprefixes = ["CO", "VG"]\n',
            'names two requests alike',
        ),
    ],
    ids=['pages-without-search', 'categories-without-observation', 'same-length-prefixes'],
)
def test_a_scenario_that_cannot_be_measured_is_refused(
    tmp_path: Path, scenarios: str, message: str
) -> None:
    """A scenario whose requests would fail, or overwrite each other's metric, fails at load."""
    path = tmp_path / 'web.toml'
    path.write_text(_SERVER + scenarios)
    with pytest.raises(ScenarioError, match=message):
        web_scenarios.load_web_config(path, scale='fixture')


def test_the_scenario_file_warms_no_state() -> None:
    """A run warms only when asked, so a plain session measures a cold start."""
    assert web_scenarios.load_web_config().warm == frozenset()


def test_the_warm_flags_name_the_states_they_warm(tmp_path: Path) -> None:
    """Each cold state takes its own flag."""
    path = tmp_path / 'web.toml'
    path.write_text(_SERVER + '[warm]\ndb-cold = true\napp-cold = false\n')
    assert web_scenarios.load_web_config(path, scale='fixture').warm == frozenset({'db-cold'})


@pytest.mark.parametrize(
    ('warm', 'message'),
    [('warm = true\n', r"names \['warm'\]"), ('db-cold = "yes"\n', 'true or false')],
    ids=['not-a-cold-state', 'not-a-boolean'],
)
def test_a_warm_flag_that_is_not_a_cold_states_boolean_is_refused(
    tmp_path: Path, warm: str, message: str
) -> None:
    """The warm state is never reset, so only the two cold states can warm."""
    path = tmp_path / 'web.toml'
    path.write_text(_SERVER + '[warm]\n' + warm)
    with pytest.raises(ScenarioError, match=message):
        web_scenarios.load_web_config(path, scale='fixture')


def test_the_written_configuration_is_one_opus_reads(tmp_path: Path) -> None:
    """Every key the harness writes is one the loader accepts, cache location included."""
    path = opus_config_file.write_opus_config(
        tmp_path / 'opus.toml',
        schema='bench_x',
        pds3_holdings=tmp_path / 'holdings',
        pds4_holdings=tmp_path / 'pds4-holdings',
        run_dir=tmp_path / 'run',
        cache_location='127.0.0.1:21211',
    )
    config = load_config(path)
    assert config.django.cache_location == '127.0.0.1:21211'
    assert config.database.schema == 'bench_x'
    assert config.paths.import_log_dir == str(tmp_path / 'run' / 'logs')


def test_a_session_sets_import_keys_the_loader_reads(tmp_path: Path) -> None:
    """``--import-key`` values reach the side's configuration with their types."""
    path = opus_config_file.write_opus_config(
        tmp_path / 'opus.toml',
        schema='bench_x',
        pds3_holdings=tmp_path / 'holdings',
        pds4_holdings=tmp_path / 'pds4-holdings',
        run_dir=tmp_path / 'run',
        cache_location='127.0.0.1:21211',
        extra_import=opus_config_file.parse_import_keys(
            ['index_workers=22', 'bulk_load=false', 'server_tmpdir=/var/tmp/x']
        ),
    )
    config = load_config(path)
    assert config.import_.index_workers == 22
    assert config.import_.bulk_load is False
    assert config.import_.server_tmpdir == '/var/tmp/x'


def test_a_harness_import_key_given_by_its_caller_is_written_once(tmp_path: Path) -> None:
    """``log_file`` passed to `write_opus_config` replaces the harness's own, once."""
    path = opus_config_file.write_opus_config(
        tmp_path / 'opus.toml',
        schema='bench_x',
        pds3_holdings=tmp_path / 'holdings',
        pds4_holdings=tmp_path / 'pds4-holdings',
        run_dir=tmp_path / 'run',
        cache_location='127.0.0.1:21211',
        extra_import={'log_file': str(tmp_path / 'mine.log')},
    )
    assert load_config(path).import_.log_file == str(tmp_path / 'mine.log')


def test_a_control_character_in_an_import_value_survives_the_configuration(
    tmp_path: Path,
) -> None:
    """A newline in a value is escaped rather than breaking the file."""
    path = opus_config_file.write_opus_config(
        tmp_path / 'opus.toml',
        schema='bench_x',
        pds3_holdings=tmp_path / 'holdings',
        pds4_holdings=tmp_path / 'pds4-holdings',
        run_dir=tmp_path / 'run',
        cache_location='127.0.0.1:21211',
        extra_import=opus_config_file.parse_import_keys(['server_tmpdir=/var/tmp/a\nb\x7f']),
    )
    assert load_config(path).import_.server_tmpdir == '/var/tmp/a\nb\x7f'


@pytest.mark.parametrize(
    ('text', 'value'),
    [
        ('22', 22),
        ('-3', -3),
        ('0.5', 0.5),
        ('1e-1', 0.1),
        ('true', True),
        ('false', False),
        ('nan', 'nan'),
        ('inf', 'inf'),
        ('--2', '--2'),
        ('a-1', 'a-1'),
    ],
)
def test_an_import_key_value_is_a_number_a_boolean_or_else_a_string(
    text: str, value: object
) -> None:
    """A value that does not read as a finite number or a boolean stays as written."""
    assert opus_config_file.parse_import_keys([f'k={text}']) == {'k': value}


@pytest.mark.parametrize('pair', ['index_workers', '=3'])
def test_an_import_key_without_a_key_and_value_is_refused(pair: str) -> None:
    """Each ``--import-key`` is ``KEY=VALUE``."""
    with pytest.raises(ValueError, match='KEY=VALUE'):
        opus_config_file.parse_import_keys([pair])


@pytest.mark.parametrize('pair', ['index workers=2', 'index.workers=2', 'a"b=1'])
def test_an_import_key_that_is_not_a_key_name_is_refused(pair: str) -> None:
    """A key TOML would not read bare is refused before any configuration is written."""
    with pytest.raises(ValueError, match='not an \\[import\\] key name'):
        opus_config_file.parse_import_keys([pair])


@pytest.mark.parametrize('key', opus_config_file.HARNESS_IMPORT_KEYS)
def test_an_import_key_naming_a_log_the_harness_reads_is_refused(key: str) -> None:
    """The harness reads its runs' logs from where it put them."""
    with pytest.raises(ValueError, match='the harness sets'):
        opus_config_file.parse_import_keys([f'{key}=/tmp/x.log'])


def test_a_thread_sweep_s_overrides_change_only_what_they_name() -> None:
    """The threads, the users and the scenario list each change alone."""
    config = web_scenarios.load_web_config()
    assert config.concurrency is not None
    swept = web_scenarios.with_overrides(config, threads=8, users=64, concurrency_only=True)
    assert swept.server.threads == 8
    assert swept.server.workers == config.server.workers
    assert swept.concurrency is not None
    assert swept.concurrency.users == 64
    assert swept.concurrency.distinct == config.concurrency.distinct
    assert swept.scenarios == ()
    assert web_scenarios.with_overrides(config) == config


def test_sixty_four_concurrent_users_ask_for_distinct_searches() -> None:
    """The sweep's user count still gives every user a search of its own."""
    config = web_scenarios.with_overrides(web_scenarios.load_web_config(), users=64)
    concurrency = config.concurrency
    assert concurrency is not None
    distinct = [concurrency.distinct.format(i=i) for i in range(concurrency.users)]
    assert len(set(distinct)) == 64
    assert concurrency.shared not in distinct


@pytest.mark.parametrize(
    ('threads', 'users', 'message'),
    [(0, None, 'threads'), (None, 0, 'users')],
)
def test_a_count_below_one_is_refused(threads: int | None, users: int | None, message: str) -> None:
    """No server serves with no threads, and no scenario runs with no users."""
    with pytest.raises(ScenarioError, match=message):
        web_scenarios.with_overrides(web_scenarios.load_web_config(), threads=threads, users=users)


def test_concurrency_overrides_need_a_concurrency_scenario(tmp_path: Path) -> None:
    """A file without the scenario cannot have its users changed or run it alone."""
    path = tmp_path / 'web.toml'
    path.write_text(
        '[server]\nport = 1\nworkers = 1\nthreads = 1\nmemcached_port = 2\nmemcached_mb = 8\n'
        '[runs]\nfixture = 1\n[searches]\nempty = ""\n',
        encoding='utf-8',
    )
    config = web_scenarios.load_web_config(path, scale='fixture')
    with pytest.raises(ScenarioError, match='no concurrency scenario'):
        web_scenarios.with_overrides(config, users=4)
    with pytest.raises(ScenarioError, match='no concurrency scenario'):
        web_scenarios.with_overrides(config, concurrency_only=True)
