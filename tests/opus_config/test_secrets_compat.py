"""Tests for the transitional legacy-secrets loader."""

import re
import sys
from pathlib import Path

import pytest

from opus_config._secrets_compat import (
    OPUS_SECRETS_ENV_VAR,
    SECRETS_FILENAME,
    load_secrets,
    secrets_path,
)

SECRETS_SOURCE = "DB_SCHEMA_NAME = 'opus_test_db'\nIMPORT_TABLE_TEMP_PREFIX = 'imp_'\n"


def _write_secrets(directory: Path, source: str = SECRETS_SOURCE) -> Path:
    """Write a secrets file into `directory` and return its path."""
    path = directory / SECRETS_FILENAME
    path.write_text(source)
    return path


def test_secrets_path_uses_env_var(tmp_path: Path,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """An absolute path in the environment variable wins over the directory search."""
    target = tmp_path / 'install-a' / 'secrets.py'
    monkeypatch.setenv(OPUS_SECRETS_ENV_VAR, str(target))
    assert secrets_path() == target


def test_secrets_path_falls_back_to_cwd(tmp_path: Path,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    """With no environment variable the file is looked for in the working directory."""
    monkeypatch.delenv(OPUS_SECRETS_ENV_VAR, raising=False)
    monkeypatch.chdir(tmp_path)
    assert secrets_path() == tmp_path / SECRETS_FILENAME


def test_secrets_path_ignores_empty_env_var(tmp_path: Path,
                                            monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty variable is treated as unset rather than as the current directory."""
    monkeypatch.setenv(OPUS_SECRETS_ENV_VAR, '')
    monkeypatch.chdir(tmp_path)
    assert secrets_path() == tmp_path / SECRETS_FILENAME


def test_load_secrets_exposes_attributes(tmp_path: Path,
                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """Every name defined in the secrets file is an attribute of the loaded module."""
    monkeypatch.setenv(OPUS_SECRETS_ENV_VAR, str(_write_secrets(tmp_path)))
    secrets = load_secrets()
    assert secrets.DB_SCHEMA_NAME == 'opus_test_db'
    assert secrets.IMPORT_TABLE_TEMP_PREFIX == 'imp_'


def test_load_secrets_from_cwd(tmp_path: Path,
                               monkeypatch: pytest.MonkeyPatch) -> None:
    """The working-directory fallback loads the same file the CI scripts write."""
    monkeypatch.delenv(OPUS_SECRETS_ENV_VAR, raising=False)
    _write_secrets(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert load_secrets().DB_SCHEMA_NAME == 'opus_test_db'


def test_load_secrets_is_cached(tmp_path: Path,
                                monkeypatch: pytest.MonkeyPatch) -> None:
    """The file is executed once per process, as ``import opus_secrets`` was."""
    path = _write_secrets(tmp_path)
    monkeypatch.setenv(OPUS_SECRETS_ENV_VAR, str(path))
    first = load_secrets()
    path.write_text("DB_SCHEMA_NAME = 'changed'\n")
    assert load_secrets() is first
    assert load_secrets().DB_SCHEMA_NAME == 'opus_test_db'


def test_load_secrets_does_not_register_module(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A stray ``import opus_secrets`` must still fail rather than silently work."""
    monkeypatch.setenv(OPUS_SECRETS_ENV_VAR, str(_write_secrets(tmp_path)))
    load_secrets()
    assert 'opus_secrets' not in sys.modules


def test_load_secrets_reports_missing_file(tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing file names both the path tried and the variable that overrides it."""
    missing = tmp_path / 'nowhere' / SECRETS_FILENAME
    monkeypatch.setenv(OPUS_SECRETS_ENV_VAR, str(missing))
    with pytest.raises(FileNotFoundError, match=re.escape(str(missing))) as excinfo:
        load_secrets()
    assert OPUS_SECRETS_ENV_VAR in str(excinfo.value)


def test_load_secrets_rejects_a_directory(tmp_path: Path,
                                          monkeypatch: pytest.MonkeyPatch) -> None:
    """The variable must point at the file itself, not at its directory."""
    monkeypatch.setenv(OPUS_SECRETS_ENV_VAR, str(tmp_path))
    with pytest.raises(FileNotFoundError, match=re.escape(str(tmp_path))):
        load_secrets()


def test_load_secrets_propagates_file_errors(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An error raised while executing the secrets file is not swallowed."""
    monkeypatch.setenv(OPUS_SECRETS_ENV_VAR,
                       str(_write_secrets(tmp_path, 'raise RuntimeError("bad config")\n')))
    with pytest.raises(RuntimeError, match='bad config'):
        load_secrets()
