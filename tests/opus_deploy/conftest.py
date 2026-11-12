"""A stand-in for running a deploy script of the chain, shared by the deploy tests.

A deploy script stops a web server and installs distributions, so it never runs for real
here. It is run instead from a copy of the chain whose helper files -- the ones that read
``deploy.env``, build the installation, check the schema version and promote it -- are
replaced by stubs, with every command it runs (``sudo``, ``pip``, ``opus_manage``,
``opus_import``) a fake on ``PATH`` that records its arguments. What is left is the
script's own sequence, which is the part the tests pin. The deploy lock
(``_deploy_lock.sh``) and the promotion's steps (``_promote_steps.sh``) are the chain's
own.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
from typing import TYPE_CHECKING

from opus_deploy import scripts

if TYPE_CHECKING:
    from pathlib import Path

#: The helpers the scripts source that are replaced by stubs which do nothing. The
#: deploy.env reader, the schema version check and the promotion have stubs of their own.
_STUBBED_HELPERS = (
    '_activate_deploy_venv.sh',
    '_chain_version.sh',
    '_opus_setup_environment.sh',
)

#: The commands the scripts run, each a fake that records how it was called.
_FAKE_COMMANDS = ('sudo', 'pip', 'opus_manage', 'opus_import')

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


def run_deploy(
    tmp_path: Path, script: str, *arguments: str, migration_check: str = 'clean'
) -> tuple[int, str, list[str]]:
    """Run a deploy script with its helpers stubbed and its commands faked.

    Parameters:
        tmp_path: A scratch directory.
        script: The script, inside the chain (``import_and_deploy/<name>.sh``).
        arguments: The script's arguments.
        migration_check: What ``opus_manage migrate --plan --check`` finds: ``'clean'``,
            ``'pending'`` for a migration to apply, or ``'broken'`` for a Django that
            cannot start.

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
    deployed.mkdir(parents=True)
    (deployed / 'opus.toml').write_text('schema = "served"\n', encoding='utf-8')
    (helpers / '_read_deploy_env.sh').write_text(
        f'OPUS_DIR={opus_dir(tmp_path)}\n', encoding='utf-8'
    )
    for helper in _STUBBED_HELPERS:
        (helpers / helper).write_text(':\n', encoding='utf-8')
    calls = tmp_path / 'calls'
    (helpers / '_promote.sh').write_text(
        'if flock -n "${OPUS_DIR}/deploy.lock" true; then lock=free; else lock=held; fi\n'
        f'echo "promote warm=${{OPUS_WARM_SEARCH:-true}} lock=${{lock}}" >> {calls}\n',
        encoding='utf-8',
    )
    (helpers / '_check_schema_version.sh').write_text(
        'check_schema_version() { return 0; }\n', encoding='utf-8'
    )

    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    for command in _FAKE_COMMANDS:
        status = (
            f'[[ "$*" == "migrate --plan --check" ]] && {{ {MIGRATION_CHECKS[migration_check]}; }}'
            if command == 'opus_manage'
            else ':'
        )
        fake = fake_bin / command
        fake.write_text(
            f'#!/bin/bash\necho "{command} $*" >> {calls}\n{status}\nexit 0\n', encoding='utf-8'
        )
        fake.chmod(0o755)

    assert BASH is not None
    finished = subprocess.run(  # nosec B603 - bash and the packaged script
        [BASH, str(chain / script), *arguments],
        env={'PATH': f'{fake_bin}:/usr/bin:/bin', 'HOSTNAME': 'test'},
        capture_output=True,
        text=True,
        check=False,
    )
    ran = calls.read_text(encoding='utf-8').splitlines() if calls.exists() else []
    return finished.returncode, finished.stdout + finished.stderr, ran
