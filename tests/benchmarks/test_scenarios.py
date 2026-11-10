"""The scenario files, their loaders, and their agreement with the sequences they copy."""

import re
import shlex
from pathlib import Path

import pytest

from benchmarks import bench_server, import_scenarios, web_scenarios
from benchmarks.app_servers import ServerError
from benchmarks.web_scenarios import ScenarioError
from opus_config import load_config
from opus_import import import_all

REPO_ROOT = Path(__file__).resolve().parents[2]
IMPORT_FOR_TESTS = REPO_ROOT / 'scripts' / 'import' / 'import_for_tests.sh'


def _script_groups() -> list[tuple[str, tuple[str, ...]]]:
    """Return each active bundle-import line of import_for_tests.sh: bundles, options."""
    groups = []
    for line in IMPORT_FOR_TESTS.read_text().splitlines():
        if not re.match(r'^python -m opus_import .*--import ', line):
            continue
        words = [word for word in shlex.split(line)[3:] if word != '$1']
        options = tuple(word for word in words if word.startswith('--') and word != '--import')
        bundles = [word for word in words if not word.startswith('--')]
        groups.append((bundles[0], options))
    return groups


def test_the_test_scale_groups_are_import_for_tests_sh_s(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same bundles, same order, same options, as the script the API goldens come from."""
    monkeypatch.setenv('PDS_DROPBOX_ROOT', '/holdings-root')
    scenario = import_scenarios.load_scenario('test')
    assert [(group.bundles, group.options) for group in scenario.groups] == _script_groups()


def test_the_complete_scale_groups_are_opus_import_all_s(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same bundle sets, order and options as the full-holdings import runs."""
    monkeypatch.setenv('PDS_DROPBOX_ROOT', '/holdings-root')
    scenario = import_scenarios.load_scenario('complete')
    expected = [
        (
            step[-1],
            tuple(option for option in step if option != '--import' and option != step[-1]),
        )
        for step in import_all.import_steps(None, [])
        if '--import' in step
    ]
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


def test_the_written_configuration_is_one_opus_reads(tmp_path: Path) -> None:
    """Every key the harness writes is one the loader accepts, cache location included."""
    path = bench_server.write_opus_config(
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
    path = bench_server.write_opus_config(
        tmp_path / 'opus.toml',
        schema='bench_x',
        pds3_holdings=tmp_path / 'holdings',
        pds4_holdings=tmp_path / 'pds4-holdings',
        run_dir=tmp_path / 'run',
        cache_location='127.0.0.1:21211',
        extra_import=bench_server.parse_import_keys(
            ['index_workers=22', 'bulk_load=false', 'server_tmpdir=/var/tmp/x']
        ),
    )
    config = load_config(path)
    assert config.import_.index_workers == 22
    assert config.import_.bulk_load is False
    assert config.import_.server_tmpdir == '/var/tmp/x'


def test_a_harness_import_key_given_by_its_caller_is_written_once(tmp_path: Path) -> None:
    """``log_file`` passed to `write_opus_config` replaces the harness's own, once."""
    path = bench_server.write_opus_config(
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
    path = bench_server.write_opus_config(
        tmp_path / 'opus.toml',
        schema='bench_x',
        pds3_holdings=tmp_path / 'holdings',
        pds4_holdings=tmp_path / 'pds4-holdings',
        run_dir=tmp_path / 'run',
        cache_location='127.0.0.1:21211',
        extra_import=bench_server.parse_import_keys(['server_tmpdir=/var/tmp/a\nb\x7f']),
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
    assert bench_server.parse_import_keys([f'k={text}']) == {'k': value}


@pytest.mark.parametrize('pair', ['index_workers', '=3'])
def test_an_import_key_without_a_key_and_value_is_refused(pair: str) -> None:
    """Each ``--import-key`` is ``KEY=VALUE``."""
    with pytest.raises(ValueError, match='KEY=VALUE'):
        bench_server.parse_import_keys([pair])


@pytest.mark.parametrize('pair', ['index workers=2', 'index.workers=2', 'a"b=1'])
def test_an_import_key_that_is_not_a_key_name_is_refused(pair: str) -> None:
    """A key TOML would not read bare is refused before any configuration is written."""
    with pytest.raises(ValueError, match='not an \\[import\\] key name'):
        bench_server.parse_import_keys([pair])


@pytest.mark.parametrize('key', bench_server.HARNESS_IMPORT_KEYS)
def test_an_import_key_naming_a_log_the_harness_reads_is_refused(key: str) -> None:
    """The harness reads its runs' logs from where it put them."""
    with pytest.raises(ValueError, match='the harness sets'):
        bench_server.parse_import_keys([f'{key}=/tmp/x.log'])
