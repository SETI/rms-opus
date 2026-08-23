"""Tests for reading and validating the OPUS configuration file.

Every OPUS process is configured by one TOML file, so a file that is accepted when it
should have been refused misconfigures a whole installation silently. These tests pin
both halves of that contract: what a valid file produces, and which invalid file is
refused with which message.
"""

import re
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from opus_config import (
    OPUS_CONFIG_ENV_VAR,
    ConfigError,
    config_path,
    get_config,
    load_config,
)

#: A configuration holding every required key and no optional one, which is what the
#: default and error cases below are built from.
MINIMAL_CONFIG = """\
[database]
host = "localhost"
schema = "opus_schema"
user = "opus_user"
password = "opus_password"

[paths]
pds3_holdings = "/holdings"
pds4_holdings = "/pds4-holdings"
opus_log_file = "/logs/opus_log.txt"
import_log_dir = "/logs/import"
tar_dir = "/downloads/tar/"
manifest_dir = "/downloads/manifest/"
last_blog_update_file = "/data/last_update.txt"
notification_file = "/data/notification.html"
opus_static_root = "/static_media"

[django]
secret_key = "fred"
debug = true
allowed_hosts = ["127.0.0.1", "localhost"]
cache_server_prefix = "staging_test"
public_url = "https://opus.example.org/"
product_http_path = "https://products.example.org/"
viewmaster_url = "https://viewmaster.example.org/"
tar_file_url = "https://downloads.example.org/"

[import]
log_file = "/logs/import/opus_import.log"
debug_log_file = "/logs/import/opus_import_debug.log"
"""


def replacing(key: str, value: str, *, text: str = MINIMAL_CONFIG) -> str:
    """Return a configuration with one of its keys given a different value.

    Parameters:
        key: The key to change. Every key of the schema is unique across the tables,
            so naming the table as well is unnecessary.
        value: The replacement, written as it would appear in the file.
        text: The configuration to change.

    Returns:
        The configuration text with that one line rewritten.
    """
    lines = [f'{key} = {value}' if line.startswith(f'{key} = ') else line
             for line in text.splitlines()]
    return '\n'.join(lines) + '\n'


def without(key: str, *, text: str = MINIMAL_CONFIG) -> str:
    """Return a configuration with one of its keys removed.

    Parameters:
        key: The key to drop.
        text: The configuration to change.

    Returns:
        The configuration text with that one line missing.
    """
    kept = [line for line in text.splitlines() if not line.startswith(f'{key} = ')]
    return '\n'.join(kept) + '\n'


def adding(table: str, key: str, value: str, *, text: str = MINIMAL_CONFIG) -> str:
    """Return a configuration with one key added to one of its tables.

    Parameters:
        table: Name of the table to add the key to.
        key: The key to add.
        value: Its value, written as it would appear in the file.
        text: The configuration to change.

    Returns:
        The configuration text with that line inserted under the table's header.
    """
    lines: list[str] = []
    for line in text.splitlines():
        lines.append(line)
        if line == f'[{table}]':
            lines.append(f'{key} = {value}')
    return '\n'.join(lines) + '\n'


@pytest.fixture
def write_config(tmp_path: Path) -> Callable[[str], Path]:
    """Return a function writing configuration text to a throwaway file.

    Returns:
        A function taking the text of a configuration file and returning its path.
    """
    def write(text: str) -> Path:
        path = tmp_path / 'opus.toml'
        path.write_text(text)
        return path
    return write


def test_load_config_reads_every_table(write_config: Callable[[str], Path]) -> None:
    """A complete file is read into the four tables, value for value."""
    config = load_config(write_config(MINIMAL_CONFIG))
    assert config.database.host == 'localhost'
    assert config.paths.pds4_holdings == '/pds4-holdings'
    assert config.django.secret_key == 'fred'
    assert config.import_.debug_log_file == '/logs/import/opus_import_debug.log'


def test_load_config_records_its_source(write_config: Callable[[str], Path]) -> None:
    """The configuration knows which file it came from."""
    path = write_config(MINIMAL_CONFIG)
    assert load_config(path).source == path


def test_load_config_accepts_a_path_as_a_string(
        write_config: Callable[[str], Path]) -> None:
    """The file may be named by a string as readily as by a path."""
    path = write_config(MINIMAL_CONFIG)
    assert load_config(str(path)).database.schema == 'opus_schema'


def test_load_config_keeps_values_verbatim(
        write_config: Callable[[str], Path]) -> None:
    """Paths are used exactly as written, trailing separator included.

    The web application joins these two directly to a file name, so stripping a
    trailing slash would silently write into the parent directory.
    """
    config = load_config(write_config(MINIMAL_CONFIG))
    assert config.paths.tar_dir == '/downloads/tar/'
    assert config.paths.manifest_dir == '/downloads/manifest/'


def test_load_config_reads_an_array_as_a_tuple(
        write_config: Callable[[str], Path]) -> None:
    """A string array becomes a tuple, in file order."""
    config = load_config(write_config(MINIMAL_CONFIG))
    assert config.django.allowed_hosts == ('127.0.0.1', 'localhost')


def test_load_config_is_frozen(write_config: Callable[[str], Path]) -> None:
    """A loaded configuration cannot be edited by the code that reads it."""
    config = load_config(write_config(MINIMAL_CONFIG))
    with pytest.raises(FrozenInstanceError):
        config.database.password = 'changed'  # type: ignore[misc]


@pytest.mark.parametrize(('attribute', 'expected'), [
    ('database.brand', 'MySQL'),
    ('database.database', ''),
    ('paths.static_root', None),
    ('django.log_file_level', 'INFO'),
    ('django.log_console_level', 'INFO'),
    ('django.log_django_level', 'WARNING'),
    ('django.log_api_calls', False),
    ('django.fake_api_delays', None),
    ('django.fake_error404_probability', 0.),
    ('django.fake_error500_probability', 0.),
    ('import_.table_temp_prefix', 'imp_'),
])
def test_load_config_defaults_every_optional_key(
        write_config: Callable[[str], Path], attribute: str, expected: object) -> None:
    """A file holding only the required keys still yields a complete configuration."""
    config = load_config(write_config(MINIMAL_CONFIG))
    table, key = attribute.split('.')
    assert getattr(getattr(config, table), key) == expected


@pytest.mark.parametrize(('table', 'key', 'written', 'expected'), [
    ('database', 'brand', '"PostgreSQL"', 'PostgreSQL'),
    ('database', 'database', '"opus_pg"', 'opus_pg'),
    ('paths', 'static_root', '"/production/static_media"', '/production/static_media'),
    ('django', 'fake_api_delays', '-250', -250),
    ('django', 'log_api_calls', '"debug"', 'DEBUG'),
    ('django', 'fake_error404_probability', '0.25', 0.25),
    ('django', 'log_console_level', '"CRITICAL"', 'CRITICAL'),
])
def test_load_config_reads_an_optional_key_that_is_written(
        write_config: Callable[[str], Path], table: str, key: str, written: str,
        expected: object) -> None:
    """Each optional key is honored when the file does supply it."""
    config = load_config(write_config(adding(table, key, written)))
    assert getattr(getattr(config, table), key) == expected


@pytest.mark.parametrize(('written', 'expected'), [
    ('"mysql"', 'MySQL'),
    ('"MYSQL"', 'MySQL'),
    ('"postgresql"', 'PostgreSQL'),
])
def test_load_config_canonicalizes_the_database_brand(
        write_config: Callable[[str], Path], written: str, expected: str) -> None:
    """A brand is matched without regard to case and stored in one spelling."""
    text = adding('database', 'brand', written)
    assert load_config(write_config(text)).database.brand == expected


def test_load_config_canonicalizes_a_log_level(
        write_config: Callable[[str], Path]) -> None:
    """A level is matched without regard to case, and stored as `logging` spells it."""
    text = adding('django', 'log_django_level', '"error"')
    assert load_config(write_config(text)).django.log_django_level == 'ERROR'


def test_load_config_accepts_a_whole_number_probability(
        write_config: Callable[[str], Path]) -> None:
    """A probability written without a decimal point is read as a number."""
    text = adding('django', 'fake_error500_probability', '1')
    config = load_config(write_config(text))
    assert config.django.fake_error500_probability == pytest.approx(1.)


@pytest.mark.parametrize(('text', 'message'), [
    (without('host'), "[database] is missing the required key 'host'"),
    (without('pds3_holdings'), "[paths] is missing the required key 'pds3_holdings'"),
    (without('secret_key'), "[django] is missing the required key 'secret_key'"),
    (without('log_file'), "[import] is missing the required key 'log_file'"),
    (replacing('host', '5'), "[database] 'host' must be a string, not int"),
    (replacing('debug', '"yes"'), "[django] 'debug' must be true or false, not str"),
    (replacing('allowed_hosts', '"localhost"'),
     "[django] 'allowed_hosts' must be an array of strings, not str"),
    (replacing('allowed_hosts', '["localhost", 5]'),
     "[django] every entry of 'allowed_hosts' must be a string, not int"),
    (adding('database', 'brand', '"Oracle"'),
     "[database] 'brand' must be one of MySQL, PostgreSQL, not 'Oracle'"),
    (adding('database', 'brand', '5'), "[database] 'brand' must be a string, not int"),
    (adding('django', 'log_file_level', '"CHATTY"'),
     "[django] 'log_file_level' must be one of DEBUG, INFO"),
    (adding('django', 'log_api_calls', '"CHATTY"'),
     "[django] 'log_api_calls' must be one of DEBUG, INFO"),
    (adding('django', 'log_api_calls', '5'),
     "[django] 'log_api_calls' must be true, false or one of DEBUG"),
    (adding('django', 'fake_api_delays', '"soon"'),
     "[django] 'fake_api_delays' must be a whole number, not str"),
    (adding('django', 'fake_api_delays', 'true'),
     "[django] 'fake_api_delays' must be a whole number, not bool"),
    (adding('django', 'fake_error404_probability', 'true'),
     "[django] 'fake_error404_probability' must be a number, not bool"),
    (adding('django', 'fake_error404_probability', '"often"'),
     "[django] 'fake_error404_probability' must be a number, not str"),
    (adding('database', 'hostname', '"localhost"'),
     "[database] has unknown key(s): 'hostname'"),
    (adding('import', 'temp', '"imp_"', text=adding('import', 'prefix', '"imp_"')),
     "[import] has unknown key(s): 'prefix', 'temp'"),
], ids=['missing-database-key', 'missing-paths-key', 'missing-django-key',
        'missing-import-key', 'string-key-given-a-number', 'boolean-key-given-a-string',
        'array-key-given-a-string', 'array-entry-not-a-string', 'brand-not-a-brand',
        'brand-not-a-string', 'level-not-a-level', 'log-api-calls-not-a-level',
        'log-api-calls-not-a-boolean', 'delay-not-a-number', 'delay-given-a-boolean',
        'probability-given-a-boolean', 'probability-given-a-string',
        'one-unknown-key', 'two-unknown-keys'])
def test_load_config_rejects_an_invalid_key(
        write_config: Callable[[str], Path], text: str, message: str) -> None:
    """An invalid value is refused with a message naming its table and key."""
    with pytest.raises(ConfigError, match=re.escape(message)):
        load_config(write_config(text))


@pytest.mark.parametrize(('text', 'message'), [
    (MINIMAL_CONFIG.split('[paths]')[0],
     'is missing the table(s): [paths], [django], [import]'),
    (MINIMAL_CONFIG + '\n[dictionary]\nterm_url = "https://example.org/"\n',
     "has unknown top-level entry(s): 'dictionary'"),
    ('extra = 1\n' + MINIMAL_CONFIG, "has unknown top-level entry(s): 'extra'"),
], ids=['missing-tables', 'unknown-table', 'unknown-top-level-key'])
def test_load_config_rejects_an_invalid_table(
        write_config: Callable[[str], Path], text: str, message: str) -> None:
    """A missing or unrecognized table is refused, naming the file."""
    path = write_config(text)
    with pytest.raises(ConfigError, match=re.escape(f'{path} {message}')):
        load_config(path)


def test_load_config_rejects_a_table_name_used_for_a_value(
        write_config: Callable[[str], Path]) -> None:
    """A table name bound to something that is not a table is refused."""
    text = 'import = "yes"\n' + MINIMAL_CONFIG.split('[import]')[0]
    with pytest.raises(ConfigError, match=re.escape('[import] must be a table')):
        load_config(write_config(text))


def test_load_config_rejects_invalid_toml(
        write_config: Callable[[str], Path]) -> None:
    """A file that is not TOML at all is refused as such, not as a missing table."""
    with pytest.raises(ConfigError, match='is not a valid TOML file'):
        load_config(write_config('[database\nhost = localhost\n'))


def test_load_config_rejects_a_file_that_is_not_utf8(tmp_path: Path) -> None:
    """A file in the wrong encoding is refused as an unreadable file, not as a crash.

    ``tomllib`` decodes the bytes itself, so this arrives as a `UnicodeDecodeError` rather
    than the decode error TOML parsing raises.
    """
    path = tmp_path / 'opus.toml'
    path.write_bytes(b'[database]\nhost = "\xff"\n')
    with pytest.raises(ConfigError, match='is not a valid TOML file'):
        load_config(path)


def test_load_config_reports_a_missing_file(tmp_path: Path) -> None:
    """A file that does not exist is named in the error."""
    missing = tmp_path / 'no_such_opus.toml'
    with pytest.raises(ConfigError, match=re.escape(str(missing))):
        load_config(missing)


def test_load_config_reports_a_directory(tmp_path: Path) -> None:
    """A directory given where a file belongs is refused rather than read."""
    with pytest.raises(ConfigError, match='Cannot read the OPUS configuration file'):
        load_config(tmp_path)


def test_config_path_returns_the_environment_value(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The variable holds the path of the file, and is used as written."""
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, '/etc/opus/opus.toml')
    assert config_path() == Path('/etc/opus/opus.toml')


def test_config_path_accepts_a_relative_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """A relative path is left to resolve against the working directory.

    The CI jobs set the variable to a path inside the checkout, so refusing one would
    make every job spell out an absolute path it does not know.
    """
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, 'tests/fixtures/opus_ci.toml')
    assert config_path() == Path('tests/fixtures/opus_ci.toml')


@pytest.mark.parametrize('value', [None, ''], ids=['unset', 'empty'])
def test_config_path_requires_the_environment_variable(
        monkeypatch: pytest.MonkeyPatch, value: str | None) -> None:
    """Without the variable there is nothing to fall back on, and OPUS says so."""
    if value is None:
        monkeypatch.delenv(OPUS_CONFIG_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, value)
    with pytest.raises(ConfigError, match=f'The {OPUS_CONFIG_ENV_VAR} environment '
                                          f'variable is not set'):
        config_path()


def test_get_config_reads_the_file_the_environment_names(
        write_config: Callable[[str], Path],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """`get_config` is `load_config` applied to the file `config_path` names."""
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(write_config(MINIMAL_CONFIG)))
    assert get_config().database.user == 'opus_user'


def test_get_config_reads_the_file_once(write_config: Callable[[str], Path],
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    """Every part of a process sees one configuration, however often it asks."""
    path = write_config(MINIMAL_CONFIG)
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(path))
    first = get_config()
    path.write_text(MINIMAL_CONFIG.replace('opus_user', 'someone_else'))
    assert get_config() is first


def test_get_config_rereads_after_its_cache_is_cleared(
        write_config: Callable[[str], Path],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Clearing the cache is what makes a second file take effect."""
    path = write_config(MINIMAL_CONFIG)
    monkeypatch.setenv(OPUS_CONFIG_ENV_VAR, str(path))
    assert get_config().database.user == 'opus_user'
    path.write_text(MINIMAL_CONFIG.replace('opus_user', 'someone_else'))
    get_config.cache_clear()
    assert get_config().database.user == 'someone_else'


def test_the_ci_fixture_is_a_valid_configuration(ci_config_path: Path) -> None:
    """The checked-in CI configuration loads, so no job discovers otherwise.

    It is the standing ``OPUS_CONFIG`` of every GitHub-hosted job, and nothing else in
    the unit suite would notice if it drifted out of the schema.
    """
    config = load_config(ci_config_path)
    assert config.database.schema == 'opus_ci_db'
    assert config.import_.table_temp_prefix == 'imp_'
    assert config.paths.static_root is None
