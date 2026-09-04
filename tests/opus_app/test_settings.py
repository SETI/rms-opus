"""Tests for the Django settings the OPUS configuration file supplies.

Nothing in the web application reads the configuration itself: `opus_app.settings`
reads it once and publishes each value under the name the application already uses, so
a value wired to the wrong name would reach production as a working site pointed at the
wrong directory or URL. The configuration below therefore gives every key a distinct
value, and the test asserts where each one comes out.

The settings module is imported in a subprocess, because what is being checked is what
one OPUS process reads at startup.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from opus_config import OPUS_CONFIG_ENV_VAR

#: A configuration whose every value is distinct, so that a setting read from the wrong
#: key cannot pass by holding a plausible value.
DISTINCT_CONFIG = """\
[database]
brand = "MySQL"
host = "database-host"
database = "database-database"
schema = "database-schema"
user = "database-user"
password = "database-password"

[paths]
pds3_holdings = "/paths/pds3-holdings"
pds4_holdings = "/paths/pds4-holdings"
opus_log_file = "/paths/opus-log-file.txt"
import_log_dir = "/paths/import-log-dir"
tar_dir = "/paths/tar-dir/"
manifest_dir = "/paths/manifest-dir/"
last_blog_update_file = "/paths/last-blog-update-file.txt"
notification_file = "/paths/notification-file.html"
static_root = "/paths/static-root"
opus_static_root = "/paths/opus-static-root"

[django]
secret_key = "django-secret-key"
debug = true
allowed_hosts = ["django-allowed-host-1", "django-allowed-host-2"]
cache_server_prefix = "django-cache-server-prefix"
public_url = "https://django-public-url.example.org/"
product_http_path = "https://django-product-http-path.example.org/"
viewmaster_url = "https://django-viewmaster-url.example.org/"
tar_file_url = "https://django-tar-file-url.example.org/"
log_file_level = "ERROR"
log_console_level = "CRITICAL"
log_django_level = "DEBUG"
log_api_calls = "INFO"
fake_api_delays = -125
fake_error404_probability = 0.25
fake_error500_probability = 0.75

[import]
table_temp_prefix = "import-table-temp-prefix"
log_file = "/import/log-file.log"
debug_log_file = "/import/debug-log-file.log"
"""

#: Every setting the configuration file supplies, and the value `DISTINCT_CONFIG` gives
#: it. This is the mapping `opus_app.settings` implements, written out.
EXPECTED_SETTINGS = {
    'SECRET_KEY': 'django-secret-key',
    'DEBUG': True,
    'ALLOWED_HOSTS': ['django-allowed-host-1', 'django-allowed-host-2'],
    'STATIC_ROOT': '/paths/static-root',
    'DB_HOST_NAME': 'database-host',
    'DB_SCHEMA_NAME': 'database-schema',
    'DB_USER': 'database-user',
    'DB_PASSWORD': 'database-password',
    'PDS3_DATA_DIR': '/paths/pds3-holdings',
    'PDS4_DATA_DIR': '/paths/pds4-holdings',
    'OPUS_STATIC_ROOT': '/paths/opus-static-root',
    'CACHE_SERVER_PREFIX': 'django-cache-server-prefix',
    'PUBLIC_OPUS_URL': 'https://django-public-url.example.org/',
    'PRODUCT_HTTP_PATH': 'https://django-product-http-path.example.org/',
    'VIEWMASTER_ROOT_PATH': 'https://django-viewmaster-url.example.org/',
    'TAR_FILE_PATH': '/paths/tar-dir/',
    'MANIFEST_FILE_PATH': '/paths/manifest-dir/',
    'TAR_FILE_URL_PATH': 'https://django-tar-file-url.example.org/',
    'OPUS_LAST_BLOG_UPDATE_FILE': '/paths/last-blog-update-file.txt',
    'OPUS_NOTIFICATION_FILE': '/paths/notification-file.html',
    'OPUS_LOG_FILE': '/paths/opus-log-file.txt',
    'OPUS_LOG_FILE_LEVEL': 'ERROR',
    'OPUS_LOG_CONSOLE_LEVEL': 'CRITICAL',
    'OPUS_LOG_DJANGO_LEVEL': 'DEBUG',
    'OPUS_LOG_API_CALLS': 'INFO',
    'OPUS_FAKE_API_DELAYS': -125,
    'OPUS_FAKE_SERVER_ERROR404_PROBABILITY': 0.25,
    'OPUS_FAKE_SERVER_ERROR500_PROBABILITY': 0.75,
}

_DUMP_SETTINGS = (
    'import json, sys; import opus_app.settings as settings; '
    'print(json.dumps({name: getattr(settings, name) '
    'for name in sys.argv[1:]}))'
)


def _import_settings(
    config: Path | None, directory: Path, *names: str
) -> subprocess.CompletedProcess[str]:
    """Import the settings module in a subprocess and print the settings asked for.

    Parameters:
        config: The configuration file to name in the environment, or None to run with
            no configuration at all.
        directory: Working directory for the subprocess, which no setting depends on.
        names: The settings to print, as one JSON object.

    Returns:
        The finished process, its standard output holding the JSON object when the
        import succeeded.
    """
    env = dict(os.environ)
    if config is None:
        env.pop(OPUS_CONFIG_ENV_VAR, None)
    else:
        env[OPUS_CONFIG_ENV_VAR] = str(config)
    return subprocess.run(
        [sys.executable, '-c', _DUMP_SETTINGS, *names],
        capture_output=True,
        text=True,
        cwd=directory,
        env=env,
        check=False,
    )


@pytest.fixture
def distinct_config(tmp_path: Path) -> Path:
    """Write `DISTINCT_CONFIG` to a throwaway file.

    Returns:
        The path of the written configuration file.
    """
    path = tmp_path / 'opus.toml'
    path.write_text(DISTINCT_CONFIG)
    return path


@pytest.fixture
def loaded_settings(distinct_config: Path, tmp_path: Path) -> dict[str, object]:
    """Import the settings module against `DISTINCT_CONFIG` once for every test.

    Returns:
        Every setting of `EXPECTED_SETTINGS`, as the settings module publishes it.
    """
    result = _import_settings(distinct_config, tmp_path, *EXPECTED_SETTINGS)
    assert result.returncode == 0, result.stderr
    loaded: dict[str, object] = json.loads(result.stdout)
    return loaded


@pytest.mark.parametrize('name', list(EXPECTED_SETTINGS))
def test_settings_publish_the_configured_value(
    loaded_settings: dict[str, object], name: str
) -> None:
    """Each setting holds the value its own configuration key supplies."""
    assert loaded_settings[name] == EXPECTED_SETTINGS[name]


def test_allowed_hosts_is_a_list(loaded_settings: dict[str, object]) -> None:
    """Django documents ALLOWED_HOSTS as a list, whatever the file's array becomes."""
    assert isinstance(loaded_settings['ALLOWED_HOSTS'], list)


@pytest.mark.parametrize(
    ('brand', 'engine'),
    [
        ('MySQL', 'django.db.backends.mysql'),
        ('PostgreSQL', 'django.db.backends.postgresql'),
    ],
)
def test_database_engine_follows_the_configured_brand(
    tmp_path: Path, brand: str, engine: str
) -> None:
    """The engine is selected from the brand the import pipeline reads from too.

    Were it hardcoded, a configuration naming one brand would drive the import pipeline
    and the web application at two different databases without saying so.
    """
    path = tmp_path / 'opus.toml'
    path.write_text(DISTINCT_CONFIG.replace('brand = "MySQL"', f'brand = "{brand}"'))
    result = _import_settings(path, tmp_path, 'DATABASES')
    assert result.returncode == 0, result.stderr
    databases: dict[str, dict[str, str]] = json.loads(result.stdout)['DATABASES']
    assert databases['default']['ENGINE'] == engine


def test_settings_omit_static_root_when_the_file_does(tmp_path: Path) -> None:
    """A configuration without static_root leaves Django's own default in place.

    A development or test installation never runs collectstatic, so it has nothing to
    point the setting at.
    """
    path = tmp_path / 'opus.toml'
    path.write_text(DISTINCT_CONFIG.replace('static_root = "/paths/static-root"\n', ''))
    result = _import_settings(path, tmp_path, 'STATIC_ROOT')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {'STATIC_ROOT': None}


def test_settings_require_the_configuration_variable(tmp_path: Path) -> None:
    """Without OPUS_CONFIG the site refuses to start, naming the variable to set."""
    result = _import_settings(None, tmp_path, 'SECRET_KEY')
    assert result.returncode != 0
    assert OPUS_CONFIG_ENV_VAR in result.stderr
    assert 'ConfigError' in result.stderr


def test_settings_report_an_invalid_configuration(tmp_path: Path) -> None:
    """An invalid configuration stops the site with the file and the key named."""
    path = tmp_path / 'opus.toml'
    path.write_text(DISTINCT_CONFIG.replace('secret_key = "django-secret-key"\n', ''))
    result = _import_settings(path, tmp_path, 'SECRET_KEY')
    assert result.returncode != 0
    assert "[django] is missing the required key 'secret_key'" in result.stderr
