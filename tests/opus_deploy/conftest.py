"""A stand-in for running a deploy script of the chain, shared by the deploy tests.

A deploy script stops a web server and installs distributions, so it never runs for real
here. It is run instead from a copy of the chain whose helper files -- the ones that read
``deploy.env``, build the installation, check the schema version and promote it -- are
replaced by stubs, as are ``database/dump_db.sh`` and ``database/load_db.sh``, with every
command it runs (``sudo``, ``pip``, ``opus_manage``, ``opus_import`` and the rest of
`FAKE_COMMANDS`) a fake on ``PATH`` that records its arguments. What is left is the
script's own sequence, which is the part the tests pin. The deploy lock
(``_deploy_lock.sh``), the promotion's steps (``_promote_steps.sh``) and every other
sourced file are the chain's own.
"""

from __future__ import annotations

import shlex
import shutil
import subprocess  # nosec B404
from typing import TYPE_CHECKING

from opus_deploy import scripts
from opus_import.steps.do_generation import GENERATION_REFUSED_EXIT_STATUS

if TYPE_CHECKING:
    from pathlib import Path

#: The helpers the scripts source that are replaced by stubs which do nothing. The
#: deploy.env reader, the schema version check and the promotion have stubs of their own.
_STUBBED_HELPERS = (
    '_activate_deploy_venv.sh',
    '_chain_version.sh',
    '_opus_setup_environment.sh',
)

#: The commands the scripts run, each a fake that records how it was called. ``nohup``
#: records and runs nothing.
FAKE_COMMANDS = (
    'sudo',
    'pip',
    'opus_manage',
    'opus_import',
    'opus_import_all',
    'nohup',
    'mail',
)

#: The chain's database scripts, each replaced by a stub that records how it was called.
_STUBBED_DATABASE_SCRIPTS = ('dump_db.sh', 'load_db.sh')

#: The two service units the stand-in ``deploy.env`` names.
WEB_SERVICE = 'opus-web'
CACHE_SERVICE = 'opus-cache'

#: Bash, which the scripts are run with; None where it is not installed.
BASH = shutil.which('bash')

#: What the fake ``opus_manage migrate --plan --check`` does for each case, as Django does.
MIGRATION_CHECKS = {
    'clean': 'echo "Planned operations:"; echo "  No planned migration operations."; exit 0',
    'pending': 'echo "Planned operations:"; echo "sessions.0002_x"; exit 1',
    'broken': 'echo "django.core.exceptions.ImproperlyConfigured: no settings" >&2; exit 1',
}


def opus_dir(tmp_path: Path) -> Path:
    """Return the OPUS directory `run_deploy` names in its stand-in ``deploy.env``.

    Parameters:
        tmp_path: The scratch directory given to `run_deploy`.

    Returns:
        The directory, whose ``deployed/opus.toml`` names the schema ``served``, and where
        the deploy lock is ``deploy.lock``.
    """
    return tmp_path / 'opus'


def write_recorder(path: Path, calls: Path, body: str = '') -> None:
    """Write an executable bash script that appends its name and arguments to a file.

    Parameters:
        path: Where the script goes; its name is what it records.
        calls: The file each call is appended to, one line a call.
        body: Bash run after the call is recorded; the script exits 0 when this does not
            exit first.
    """
    path.write_text(
        f'#!/bin/bash\necho "{path.name} $*" >> {shlex.quote(str(calls))}\n{body}\nexit 0\n',
        encoding='utf-8',
    )
    path.chmod(0o755)


def run_deploy(
    tmp_path: Path,
    script: str,
    *arguments: str,
    migration_check: str = 'clean',
    failing_import: str | None = None,
    refused_import: str | None = None,
    web_service_active: bool = True,
    deploy_env: dict[str, str] | None = None,
    deployed_schema: str | None = 'served',
    deployed_release: str = '3.25.0',
    generation_refusal: str = '',
    failing_sudo: str | None = None,
) -> tuple[int, str, list[str]]:
    """Run a deploy script with its helpers stubbed and its commands faked.

    Parameters:
        tmp_path: A scratch directory.
        script: The script, inside the chain (``import_and_deploy/<name>.sh``).
        arguments: The script's arguments.
        migration_check: What ``opus_manage migrate --plan --check`` finds: ``'clean'``,
            ``'pending'`` for a migration to apply, or ``'broken'`` for a Django that
            cannot start.
        failing_import: The arguments, joined by spaces, for which the fake
            ``opus_import`` exits 1; every other call exits 0.
        refused_import: The arguments, joined by spaces, for which the fake
            ``opus_import`` exits with the status of a refused generation command.
        web_service_active: What the fake ``systemctl is-active`` answers. It is not
            recorded.
        deploy_env: Further variables the stand-in ``deploy.env`` sets, beside
            ``OPUS_DIR`` and the two services (`WEB_SERVICE`, `CACHE_SERVICE`).
        deployed_schema: The schema the deployed installation's ``opus.toml`` names, or
            None for an ``opus.toml`` that names none.
        deployed_release: The rms-opus release the deployed installation's own
            interpreter reports; empty for one that cannot report it.
        generation_refusal: What the fake ``python`` prints when asked why a switch or a
            revert would be refused; empty when it would run. It is not recorded.
        failing_sudo: The arguments, joined by spaces, for which the fake ``sudo`` exits
            1, as sudo does when its password is mistyped; every other call exits 0.

    Returns:
        The script's status, everything it printed, and each faked command it ran, as its
        name and arguments. The promotion is recorded as ``promote warm=<OPUS_WARM_SEARCH,
        or true> lock=<held or free>``, the deploy lock's state as another process finds
        it during the promotion.
    """
    chain = tmp_path / 'chain'
    scripts.write_scripts(chain)
    helpers = chain / 'import_and_deploy'
    deployed = opus_dir(tmp_path) / 'deployed'
    (deployed / 'opus_venv' / 'bin').mkdir(parents=True)
    (deployed / 'opus_venv' / 'bin' / 'activate').write_text(':\n', encoding='utf-8')
    deployed_python = deployed / 'opus_venv' / 'bin' / 'python'
    deployed_python.write_text(
        f'#!/bin/sh\necho {shlex.quote(deployed_release)}\n', encoding='utf-8'
    )
    deployed_python.chmod(0o755)
    (deployed / 'opus.toml').write_text(
        '' if deployed_schema is None else f'schema = "{deployed_schema}"\n', encoding='utf-8'
    )
    settings = {
        'OPUS_DIR': str(opus_dir(tmp_path)),
        'OPUS_WEB_SERVICE': WEB_SERVICE,
        'OPUS_CACHE_SERVICE': CACHE_SERVICE,
        **(deploy_env or {}),
    }
    (helpers / '_read_deploy_env.sh').write_text(
        ''.join(f'{name}={shlex.quote(value)}\n' for name, value in settings.items()),
        encoding='utf-8',
    )
    for helper in _STUBBED_HELPERS:
        (helpers / helper).write_text(':\n', encoding='utf-8')
    calls = tmp_path / 'calls'
    for database_script in _STUBBED_DATABASE_SCRIPTS:
        write_recorder(chain / 'database' / database_script, calls)
    recorded = shlex.quote(str(calls))
    (helpers / '_promote.sh').write_text(
        'if flock -n "${OPUS_DIR}/deploy.lock" true; then lock=free; else lock=held; fi\n'
        f'echo "promote warm=${{OPUS_WARM_SEARCH:-true}} lock=${{lock}}" >> {recorded}\n',
        encoding='utf-8',
    )
    (helpers / '_check_schema_version.sh').write_text(
        'check_schema_version() { return 0; }\n', encoding='utf-8'
    )

    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    statuses = {
        'sudo': f'[[ "$*" == {shlex.quote(failing_sudo)} ]] && exit 1'
        if failing_sudo is not None
        else '',
        'opus_manage': (
            f'[[ "$*" == "migrate --plan --check" ]] && {{ {MIGRATION_CHECKS[migration_check]}; }}'
        ),
        'opus_import': '\n'.join(
            [
                f'[[ "$*" == {shlex.quote(failing_import)} ]] && exit 1'
                if failing_import is not None
                else '',
                f'[[ "$*" == {shlex.quote(refused_import)} ]] && '
                f'exit {GENERATION_REFUSED_EXIT_STATUS}'
                if refused_import is not None
                else '',
            ]
        ),
    }
    for command in FAKE_COMMANDS:
        write_recorder(fake_bin / command, calls, statuses.get(command, ''))
    fake_python = fake_bin / 'python'
    fake_python.write_text(f'#!/bin/sh\necho {shlex.quote(generation_refusal)}\n', encoding='utf-8')
    fake_python.chmod(0o755)
    fake_systemctl = fake_bin / 'systemctl'
    fake_systemctl.write_text(
        f'#!/bin/sh\nexit {0 if web_service_active else 3}\n', encoding='utf-8'
    )
    fake_systemctl.chmod(0o755)

    assert BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged script
        [BASH, str(chain / script), *arguments],
        env={'PATH': f'{fake_bin}:/usr/bin:/bin', 'HOSTNAME': 'test', 'TMPDIR': str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )
    ran = calls.read_text(encoding='utf-8').splitlines() if calls.exists() else []
    return finished.returncode, finished.stdout + finished.stderr, ran


def defines_only_functions(path: Path) -> bool:
    """Return whether every top-level statement of a shell file is a function definition.

    A file that passes executes nothing when it is sourced, which is what lets a test
    source it and call one function.

    Parameters:
        path: The file.

    Returns:
        True when every non-blank, non-comment line outside a function body opens a
        function (``name() {``) and the braces balance at the end.
    """
    depth = 0
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip() == '' or line.startswith('#'):
            continue
        if depth == 0 and not line.endswith('() {'):
            return False
        depth += line.count('{') - line.count('}')
    return depth == 0
