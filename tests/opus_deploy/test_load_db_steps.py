"""Tests for the second server's load, run as a shell function.

``load_db.sh`` writes a database onto another server, so it never runs here. Its load is a
file of its own, ``_load_db_steps.sh``, that defines one function and executes nothing; it
is sourced here with a fake ``mysql`` first on ``PATH`` that answers the peer's
``ngram_token_size`` and records each call's arguments and standard input.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess  # nosec B404
import textwrap
from typing import TYPE_CHECKING

import pytest

from opus_deploy import scripts

if TYPE_CHECKING:
    from pathlib import Path

#: The load, inside the packaged chain.
_STEPS = 'database/_load_db_steps.sh'

#: The statement the load's session runs before the dump.
_STOPWORDS_OFF = 'SET SESSION innodb_ft_enable_stopword = OFF;\n'

#: A dump's text, with the FULLTEXT key a real one declares.
_DUMP = (
    'CREATE TABLE `obs_pds` (\n'
    '  `bundle_id` varchar(75),\n'
    '  FULLTEXT KEY `bundle_id` (`bundle_id`) /*!50100 WITH PARSER `ngram` */\n'
    ');\n'
    "INSERT INTO `obs_pds` VALUES ('COISS_2002');\n"
)

_BASH = shutil.which('bash')


def _run_load(
    tmp_path: Path, token_size: str, *, dump_name: str = 'opus_x.sql'
) -> tuple[int, str, list[tuple[str, str]]]:
    """Source the load with a fake mysql and call it.

    Parameters:
        tmp_path: A scratch directory.
        token_size: What the fake mysql answers for the peer's ``ngram_token_size``.
        dump_name: The dump the load is given, in `tmp_path`; only ``opus_x.sql`` is
            written.

    Returns:
        The function's status, everything it printed, and each mysql call in order, as
        its arguments one to a line and its standard input (empty for the query).
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    (tmp_path / 'opus_x.sql').write_text(_DUMP, encoding='utf-8')
    dump = tmp_path / dump_name
    calls = tmp_path / 'calls'
    calls.mkdir()
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    fake_mysql = fake_bin / 'mysql'
    fake_mysql.write_text(
        textwrap.dedent(
            f"""\
            #!/bin/bash
            n=$(ls {shlex.quote(str(calls))} | wc -l)
            call={shlex.quote(str(calls))}/$(printf '%03d' "$n")
            printf '%s\\n' "$@" > "$call.args"
            case "$*" in
                *ngram_token_size*) : > "$call.stdin"; echo '{token_size}'; exit 0 ;;
            esac
            cat > "$call.stdin"
            """
        ),
        encoding='utf-8',
    )
    fake_mysql.chmod(0o755)
    assert _BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged script
        [
            _BASH,
            '-c',
            f'source {shlex.quote(str(chain / _STEPS))}; load_dump opus_x {shlex.quote(str(dump))}',
        ],
        env={
            'PATH': f'{fake_bin}:/usr/bin:/bin',
            'OPUS_DB_USER': 'opus',
            'OPUS_DB_PASSWORD': 'secret',
            'OPUS_PEER_DB_HOST': 'peer.example.org',
        },
        capture_output=True,
        text=True,
        check=False,
    )
    recorded = [
        (
            args.read_text(encoding='utf-8'),
            args.with_suffix('.stdin').read_text(encoding='utf-8'),
        )
        for args in sorted(calls.glob('*.args'))
    ]
    return finished.returncode, finished.stdout + finished.stderr, recorded


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_a_peer_with_token_size_two_is_created_and_loaded_without_stopwords(
    tmp_path: Path,
) -> None:
    """One CREATE DATABASE, then the dump unchanged on a session that first turns the
    stopword list off."""
    status, output, calls = _run_load(tmp_path, '2')
    assert status == 0, output
    query, create, load = calls
    assert 'SELECT @@GLOBAL.ngram_token_size' in query[0]
    assert create[1] == 'CREATE DATABASE opus_x;\n'
    assert load[0].splitlines()[-1] == 'opus_x'
    assert load[1] == _STOPWORDS_OFF + _DUMP
    assert sum(stdin.count('CREATE DATABASE') for _, stdin in calls) == 1


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_a_peer_with_another_token_size_is_refused_before_anything_is_created(
    tmp_path: Path,
) -> None:
    """A non-zero status and the reason, with no CREATE DATABASE and no load."""
    status, output, calls = _run_load(tmp_path, '3')
    assert status == 1
    assert 'peer.example.org has ngram_token_size = 3' in output
    assert 'only when it starts' in output
    assert len(calls) == 1
    assert 'SELECT @@GLOBAL.ngram_token_size' in calls[0][0]


@pytest.mark.skipif(_BASH is None, reason='needs bash')
def test_a_dump_that_cannot_be_read_fails_the_load(tmp_path: Path) -> None:
    """A non-zero status, though mysql succeeds on the SET SESSION it is given."""
    status, output, calls = _run_load(tmp_path, '2', dump_name='missing.sql')
    assert status != 0, output
    assert calls[-1][1] == _STOPWORDS_OFF


def test_sourcing_the_load_runs_nothing(tmp_path: Path) -> None:
    """Its only top-level statement is the function, so the tests above can source it."""
    scripts.write_scripts(tmp_path)
    lines = [
        line
        for line in (tmp_path / _STEPS).read_text(encoding='utf-8').splitlines()
        if line.strip() != '' and not line.startswith('#')
    ]
    assert lines[0] == 'load_dump() {'
    assert lines[-1] == '}'
