"""Schema and loader for the OPUS configuration file.

One TOML file describes an installation of OPUS: the database it uses, the
directories it reads and writes, and the settings of the web application and of the
import pipeline. Both `opus_import` and the Django backend read it, so it is the
single place an installation is described.

The file is found through the ``OPUS_CONFIG`` environment variable, which holds its
path. There is no default location: a server hosting several OPUS installations
gives each one its own value, and a process started without the variable stops with
an error instead of picking up a neighboring installation's settings.

The loaded configuration is a tree of frozen dataclasses, one per TOML table. Every
key is checked as it is read, so a missing key, a value of the wrong type, a value
outside the set a key allows, and a misspelled key or table are all reported as a
`ConfigError` naming the file and the key, rather than surfacing much later as an
attribute error or a puzzling database failure.

Example of a complete file::

    [database]
    host = "localhost"
    schema = "opus"
    user = "opus_user"
    password = "..."

    [paths]
    pds3_holdings = "/holdings"
    pds4_holdings = "/pds4-holdings"
    opus_log_file = "/var/log/opus/opus_log.txt"
    import_log_dir = "/var/log/opus/import"
    tar_dir = "/opus/downloads/"
    manifest_dir = "/opus/manifests/"
    last_blog_update_file = "/opus/data/last_update.txt"
    notification_file = "/opus/data/notification.html"
    opus_static_root = "/opus/static_media"

    [django]
    secret_key = "..."
    debug = false
    allowed_hosts = ["127.0.0.1", "localhost"]
    cache_server_prefix = "production"
    public_url = "https://opus.pds-rings.seti.org/"
    product_http_path = "https://opus.pds-rings.seti.org/"
    viewmaster_url = "https://pds-rings.seti.org/"
    tar_file_url = "https://opus.pds-rings.seti.org/downloads/"

    [import]
    log_file = "/var/log/opus/import/opus_import.log"
    debug_log_file = "/var/log/opus/import/opus_import_debug.log"
"""

import functools
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

#: Environment variable holding the path of the configuration file.
OPUS_CONFIG_ENV_VAR = 'OPUS_CONFIG'

#: Database brands `DatabaseConfig.brand` accepts. Only MySQL is implemented; the
#: brand is carried through the import pipeline so a second backend can be added.
DATABASE_BRANDS = ('MySQL', 'PostgreSQL')

#: Logging levels the ``[django]`` level keys accept, as `logging` spells them.
LOG_LEVELS = ('DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL')

#: Names of the tables a configuration file must contain, in file order.
TABLE_NAMES = ('database', 'paths', 'django', 'import')

# Sentinel for "this key has no default", distinguishable from a default of None.
_REQUIRED = object()


class ConfigError(Exception):
    """Raised when the configuration file is missing, unreadable or invalid."""


@dataclass(frozen=True)
class DatabaseConfig:
    """The database holding the OPUS tables.

    Attributes:
        brand: The SQL brand, one of `DATABASE_BRANDS`.
        host: Host name of the database server, usually ``localhost``.
        database: Database to connect to. MySQL ignores this and uses `schema`.
        schema: Namespace the OPUS tables live in; the database name under MySQL.
        user: User to connect as. It needs table creation and deletion rights.
        password: Password for `user`.
    """

    brand: str
    host: str
    database: str
    schema: str
    user: str
    password: str


@dataclass(frozen=True)
class PathsConfig:
    """Directories and files outside the distribution that OPUS reads and writes.

    Every value is used exactly as written, so a value that is joined directly to a
    file name (`tar_dir`, `manifest_dir`) has to end with a path separator.

    Attributes:
        pds3_holdings: Root of the PDS3 holdings, holding ``volumes``, ``metadata``
            and the other PDS3 directories.
        pds4_holdings: Root of the PDS4 holdings, holding ``bundles`` and its peers.
        opus_log_file: File the web application logs to.
        import_log_dir: Directory the import pipeline writes its warning and error
            summaries to.
        tar_dir: Directory downloadable archives are built in.
        manifest_dir: Directory download manifests are written to.
        last_blog_update_file: File holding the date of the most recent blog entry.
        notification_file: File holding the HTML of any site-wide notification.
        static_root: Directory ``collectstatic`` gathers static files into, or None
            to leave Django's own default in place. A development installation, which
            never runs ``collectstatic``, omits the key.
        opus_static_root: Directory static files are served from, used to build the
            static URL prefix of standalone pages.
    """

    pds3_holdings: str
    pds4_holdings: str
    opus_log_file: str
    import_log_dir: str
    tar_dir: str
    manifest_dir: str
    last_blog_update_file: str
    notification_file: str
    static_root: str | None
    opus_static_root: str


@dataclass(frozen=True)
class DjangoConfig:
    """Settings of the OPUS web application.

    Attributes:
        secret_key: Django's secret key, unique per installation.
        debug: Django's DEBUG setting. Never true on a production server.
        allowed_hosts: Host names and addresses Django is permitted to serve.
        cache_server_prefix: Prefix for every memcached key, which lets several
            installations share one memcached without colliding.
        public_url: Public URL of this OPUS installation.
        product_http_path: Root URL products are retrieved from.
        viewmaster_url: Root URL of the viewmaster file browser.
        tar_file_url: Root URL downloadable archives are retrieved from. It is joined
            directly to a file name, so it has to end with a separator.
        log_file_level: Level above which records reach `PathsConfig.opus_log_file`.
        log_console_level: Level above which records reach the console.
        log_django_level: Level above which Django's own records are logged.
        log_api_calls: False to log no API call, or the level to log every API call
            at. Only a debugging installation sets a level.
        fake_api_delays: Milliseconds to delay every API response by, negative for a
            random delay between zero and its magnitude, or None for no delay.
        fake_error404_probability: Probability, from 0 to 1, of answering any API
            call with an HTTP 404 instead of doing the work.
        fake_error500_probability: The same for HTTP 500.
    """

    secret_key: str
    debug: bool
    allowed_hosts: tuple[str, ...]
    cache_server_prefix: str
    public_url: str
    product_http_path: str
    viewmaster_url: str
    tar_file_url: str
    log_file_level: str
    log_console_level: str
    log_django_level: str
    log_api_calls: bool | str
    fake_api_delays: int | None
    fake_error404_probability: float
    fake_error500_probability: float


@dataclass(frozen=True)
class ImportConfig:
    """Settings of the import pipeline.

    Attributes:
        table_temp_prefix: Prefix of the temporary tables an import builds before
            copying them over the permanent ones.
        log_file: File the pipeline writes its information-level log to.
        debug_log_file: File the pipeline writes its debug-level log to.
    """

    table_temp_prefix: str
    log_file: str
    debug_log_file: str


@dataclass(frozen=True)
class OpusConfig:
    """A complete OPUS configuration, as read from one TOML file.

    Attributes:
        source: Path of the file this configuration was read from.
        database: The ``[database]`` table.
        paths: The ``[paths]`` table.
        django: The ``[django]`` table.
        import_: The ``[import]`` table. The trailing underscore keeps the attribute
            out of the way of the ``import`` keyword.
    """

    source: Path
    database: DatabaseConfig
    paths: PathsConfig
    django: DjangoConfig
    import_: ImportConfig


class _TableReader:
    """Reads and checks the keys of one TOML table.

    Each key is taken by the ``read_*`` method matching its type, which removes it
    from the table; `finish` then reports whatever is left, which is how a misspelled
    key is caught instead of being silently ignored.
    """

    def __init__(self, source: Path, name: str, values: dict[str, Any]) -> None:
        """Prepare to read one table.

        Parameters:
            source: Path of the configuration file, named in every error message.
            name: Name of the table, for example ``database``.
            values: The table's contents, as parsed from the file.
        """
        self._source = source
        self._name = name
        self._values = dict(values)

    def _fail(self, message: str) -> NoReturn:
        """Report a problem with this table.

        Parameters:
            message: What is wrong, phrased to follow the table's name.

        Raises:
            ConfigError: Always.
        """
        raise ConfigError(f'{self._source}: [{self._name}] {message}')

    def _take(self, key: str, default: Any) -> Any:
        """Remove one key from the table and return its value.

        Parameters:
            key: The key to take.
            default: Value to return when the key is absent, or `_REQUIRED` to make
                the key mandatory.

        Returns:
            The key's value, or `default` when the key is absent.

        Raises:
            ConfigError: If the key is absent and no default was given.
        """
        if key in self._values:
            return self._values.pop(key)
        if default is _REQUIRED:
            self._fail(f'is missing the required key {key!r}')
        return default

    def _canonical(self, key: str, value: str, choices: tuple[str, ...]) -> str:
        """Match a string against a set of allowed values, ignoring case.

        Parameters:
            key: Name of the key the value came from.
            value: The value read from the file.
            choices: The allowed values, in their canonical spelling.

        Returns:
            The matching entry of `choices`, so that a value written in any mixture
            of cases reaches the application in one spelling.

        Raises:
            ConfigError: If the value matches no entry of `choices`.
        """
        for choice in choices:
            if value.upper() == choice.upper():
                return choice
        self._fail(f'{key!r} must be one of {", ".join(choices)}, not {value!r}')

    def read_str(self, key: str, *, default: Any = _REQUIRED) -> str:
        """Read a string.

        Parameters:
            key: The key to read.
            default: Value to use when the key is absent; by default the key is
                required.

        Returns:
            The string, exactly as written in the file.

        Raises:
            ConfigError: If the key is missing and has no default, or its value is
                not a string.
        """
        value = self._take(key, default)
        if not isinstance(value, str):
            self._fail(f'{key!r} must be a string, not {type(value).__name__}')
        return value

    def read_optional_str(self, key: str) -> str | None:
        """Read a string that may be left out of the file.

        Parameters:
            key: The key to read.

        Returns:
            The string, or None if the key is absent.

        Raises:
            ConfigError: If the key is present but its value is not a string.
        """
        if key not in self._values:
            return None
        return self.read_str(key)

    def read_choice(self, key: str, choices: tuple[str, ...], *,
                    default: Any = _REQUIRED) -> str:
        """Read a string that has to be one of a fixed set of values.

        Parameters:
            key: The key to read.
            choices: The allowed values, in their canonical spelling.
            default: Value to use when the key is absent; by default the key is
                required.

        Returns:
            The matching entry of `choices`, whatever case the file used.

        Raises:
            ConfigError: If the key is missing and has no default, its value is not a
                string, or it matches no entry of `choices`.
        """
        value = self._take(key, default)
        if not isinstance(value, str):
            self._fail(f'{key!r} must be a string, not {type(value).__name__}')
        return self._canonical(key, value, choices)

    def read_bool(self, key: str, *, default: Any = _REQUIRED) -> bool:
        """Read a boolean.

        Parameters:
            key: The key to read.
            default: Value to use when the key is absent; by default the key is
                required.

        Returns:
            The boolean.

        Raises:
            ConfigError: If the key is missing and has no default, or its value is
                not ``true`` or ``false``.
        """
        value = self._take(key, default)
        if not isinstance(value, bool):
            self._fail(f'{key!r} must be true or false, not {type(value).__name__}')
        return value

    def read_bool_or_choice(self, key: str, choices: tuple[str, ...], *,
                            default: Any = _REQUIRED) -> bool | str:
        """Read a value that is either a boolean or one of a fixed set of strings.

        Parameters:
            key: The key to read.
            choices: The allowed strings, in their canonical spelling.
            default: Value to use when the key is absent; by default the key is
                required.

        Returns:
            The boolean, or the matching entry of `choices`.

        Raises:
            ConfigError: If the key is missing and has no default, its value is
                neither a boolean nor a string, or the string matches no entry of
                `choices`.
        """
        value = self._take(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return self._canonical(key, value, choices)
        self._fail(f'{key!r} must be true, false or one of {", ".join(choices)}, '
                   f'not {type(value).__name__}')

    def read_optional_int(self, key: str) -> int | None:
        """Read a whole number that may be left out of the file.

        Parameters:
            key: The key to read.

        Returns:
            The number, or None if the key is absent.

        Raises:
            ConfigError: If the key is present but its value is not a whole number.
                A boolean is rejected even though Python counts one as an integer.
        """
        value = self._take(key, None)
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            self._fail(f'{key!r} must be a whole number, not {type(value).__name__}')
        return value

    def read_float(self, key: str, *, default: Any = _REQUIRED) -> float:
        """Read a number, accepting one written without a decimal point.

        Parameters:
            key: The key to read.
            default: Value to use when the key is absent; by default the key is
                required.

        Returns:
            The number, as a float.

        Raises:
            ConfigError: If the key is missing and has no default, or its value is
                not a number. A boolean is rejected even though Python counts one as
                an integer.
        """
        value = self._take(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            self._fail(f'{key!r} must be a number, not {type(value).__name__}')
        return float(value)

    def read_str_tuple(self, key: str) -> tuple[str, ...]:
        """Read an array of strings.

        Parameters:
            key: The key to read.

        Returns:
            The array's entries, in file order.

        Raises:
            ConfigError: If the key is missing, its value is not an array, or any
                entry is not a string.
        """
        value = self._take(key, _REQUIRED)
        if not isinstance(value, list):
            self._fail(f'{key!r} must be an array of strings, not '
                       f'{type(value).__name__}')
        for entry in value:
            if not isinstance(entry, str):
                self._fail(f'every entry of {key!r} must be a string, not '
                           f'{type(entry).__name__}')
        return tuple(value)

    def finish(self) -> None:
        """Report any key of the table that was never read.

        Raises:
            ConfigError: If the table holds a key this schema does not define, which
                is almost always a misspelling.
        """
        if len(self._values) > 0:
            unknown = ', '.join(repr(key) for key in sorted(self._values))
            self._fail(f'has unknown key(s): {unknown}')


def _read_database(source: Path, values: dict[str, Any]) -> DatabaseConfig:
    """Build the database configuration from the ``[database]`` table.

    Parameters:
        source: Path of the configuration file.
        values: Contents of the table.

    Returns:
        The validated database configuration.

    Raises:
        ConfigError: If any key is missing, of the wrong type, or unknown.
    """
    table = _TableReader(source, 'database', values)
    config = DatabaseConfig(
        brand=table.read_choice('brand', DATABASE_BRANDS, default='MySQL'),
        host=table.read_str('host'),
        database=table.read_str('database', default=''),
        schema=table.read_str('schema'),
        user=table.read_str('user'),
        password=table.read_str('password'))
    table.finish()
    return config


def _read_paths(source: Path, values: dict[str, Any]) -> PathsConfig:
    """Build the paths configuration from the ``[paths]`` table.

    Parameters:
        source: Path of the configuration file.
        values: Contents of the table.

    Returns:
        The validated paths configuration.

    Raises:
        ConfigError: If any key is missing, of the wrong type, or unknown.
    """
    table = _TableReader(source, 'paths', values)
    config = PathsConfig(
        pds3_holdings=table.read_str('pds3_holdings'),
        pds4_holdings=table.read_str('pds4_holdings'),
        opus_log_file=table.read_str('opus_log_file'),
        import_log_dir=table.read_str('import_log_dir'),
        tar_dir=table.read_str('tar_dir'),
        manifest_dir=table.read_str('manifest_dir'),
        last_blog_update_file=table.read_str('last_blog_update_file'),
        notification_file=table.read_str('notification_file'),
        static_root=table.read_optional_str('static_root'),
        opus_static_root=table.read_str('opus_static_root'))
    table.finish()
    return config


def _read_django(source: Path, values: dict[str, Any]) -> DjangoConfig:
    """Build the web application's configuration from the ``[django]`` table.

    Parameters:
        source: Path of the configuration file.
        values: Contents of the table.

    Returns:
        The validated web application configuration.

    Raises:
        ConfigError: If any key is missing, of the wrong type, outside the values it
            allows, or unknown.
    """
    table = _TableReader(source, 'django', values)
    config = DjangoConfig(
        secret_key=table.read_str('secret_key'),
        debug=table.read_bool('debug'),
        allowed_hosts=table.read_str_tuple('allowed_hosts'),
        cache_server_prefix=table.read_str('cache_server_prefix'),
        public_url=table.read_str('public_url'),
        product_http_path=table.read_str('product_http_path'),
        viewmaster_url=table.read_str('viewmaster_url'),
        tar_file_url=table.read_str('tar_file_url'),
        log_file_level=table.read_choice('log_file_level', LOG_LEVELS, default='INFO'),
        log_console_level=table.read_choice('log_console_level', LOG_LEVELS,
                                            default='INFO'),
        log_django_level=table.read_choice('log_django_level', LOG_LEVELS,
                                           default='WARN'),
        log_api_calls=table.read_bool_or_choice('log_api_calls', LOG_LEVELS,
                                                default=False),
        fake_api_delays=table.read_optional_int('fake_api_delays'),
        fake_error404_probability=table.read_float('fake_error404_probability',
                                                   default=0.),
        fake_error500_probability=table.read_float('fake_error500_probability',
                                                   default=0.))
    table.finish()
    return config


def _read_import(source: Path, values: dict[str, Any]) -> ImportConfig:
    """Build the import pipeline's configuration from the ``[import]`` table.

    Parameters:
        source: Path of the configuration file.
        values: Contents of the table.

    Returns:
        The validated import configuration.

    Raises:
        ConfigError: If any key is missing, of the wrong type, or unknown.
    """
    table = _TableReader(source, 'import', values)
    config = ImportConfig(
        table_temp_prefix=table.read_str('table_temp_prefix', default='imp_'),
        log_file=table.read_str('log_file'),
        debug_log_file=table.read_str('debug_log_file'))
    table.finish()
    return config


def _read_tables(source: Path, raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Check that the file holds exactly the tables the schema defines.

    Parameters:
        source: Path of the configuration file.
        raw: The file's contents, as parsed.

    Returns:
        The tables, keyed by name.

    Raises:
        ConfigError: If a table is missing, if the file holds a table or a key the
            schema does not define, or if a table name is used for something that is
            not a table.
    """
    missing = [name for name in TABLE_NAMES if name not in raw]
    if len(missing) > 0:
        raise ConfigError(f'{source} is missing the table(s): '
                          + ', '.join(f'[{name}]' for name in missing))
    unknown = sorted(set(raw) - set(TABLE_NAMES))
    if len(unknown) > 0:
        raise ConfigError(f'{source} has unknown top-level entry(s): '
                          + ', '.join(repr(name) for name in unknown))
    for name in TABLE_NAMES:
        if not isinstance(raw[name], dict):
            raise ConfigError(f'{source}: [{name}] must be a table')
    return {name: raw[name] for name in TABLE_NAMES}


def load_config(path: Path | str) -> OpusConfig:
    """Read and validate one configuration file.

    Parameters:
        path: Path of the file to read. A relative path is resolved against the
            working directory of the process.

    Returns:
        The configuration the file describes.

    Raises:
        ConfigError: If the file cannot be read, is not valid TOML, or does not match
            the schema. The message names the file and, where one key is at fault,
            the table and key.
    """
    source = Path(path)
    try:
        with source.open('rb') as stream:
            raw = tomllib.load(stream)
    except OSError as err:
        raise ConfigError(f'Cannot read the OPUS configuration file {source}: '
                          f'{err.strerror}') from err
    except tomllib.TOMLDecodeError as err:
        raise ConfigError(f'{source} is not a valid TOML file: {err}') from err

    tables = _read_tables(source, raw)
    return OpusConfig(
        source=source,
        database=_read_database(source, tables['database']),
        paths=_read_paths(source, tables['paths']),
        django=_read_django(source, tables['django']),
        import_=_read_import(source, tables['import']))


def config_path() -> Path:
    """Return the path of the configuration file the environment names.

    Returns:
        The path held by ``OPUS_CONFIG``. A relative path is resolved against the
        working directory of the process.

    Raises:
        ConfigError: If ``OPUS_CONFIG`` is unset or empty. There is no default
            location, so this is fatal rather than a reason to guess.
    """
    value = os.environ.get(OPUS_CONFIG_ENV_VAR)
    if value is None or value == '':
        raise ConfigError(
            f'The {OPUS_CONFIG_ENV_VAR} environment variable is not set. Set it to '
            f'the path of the OPUS configuration file; OPUS has no default location '
            f'for it.')
    return Path(value)


@functools.cache
def get_config() -> OpusConfig:
    """Return the configuration named by ``OPUS_CONFIG``.

    The file is read the first time this is called and the result is kept, so every
    part of a process sees one configuration however often they ask for it. Call
    ``get_config.cache_clear()`` to make the next call read the file again.

    Returns:
        The configuration the file describes.

    Raises:
        ConfigError: If ``OPUS_CONFIG`` is unset or empty, or the file it names
            cannot be read or does not match the schema.
    """
    return load_config(config_path())
