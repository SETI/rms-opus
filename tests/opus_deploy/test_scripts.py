"""Tests for the command that writes the server deploy chain out of the installation.

The chain is shell, and none of it can run here -- it stops a web server and installs
distributions. What these pin is the part that is this project's rather than the
operator's: that the chain really ships inside the wheel, that a copy comes out whole and
runnable, and that a copy is never quietly written over one that may already hold an
edited ``secrets/deploy.env`` beside it.
"""

import importlib.metadata
import os
import stat
from pathlib import Path

import pytest

from opus_deploy import scripts

#: One file from each directory of the chain, named so that a tree that ships only its
#: top level fails rather than passing on the strength of one file.
EXPECTED_FILES = (
    Path('README.txt'),
    Path('deploy.env.template'),
    Path('import_and_deploy/deploy_new_code_and_database.sh'),
    Path('import_and_deploy/_read_deploy_env.sh'),
    Path('database/dump_db.sh'),
    Path('log_analyzer/run_log_analyzer_update.sh_template'),
)


def test_the_chain_ships_inside_the_distribution(tmp_path: Path) -> None:
    """Every directory of it, not just the top: this is what package data gets wrong."""
    scripts.write_scripts(tmp_path)

    missing = [str(name) for name in EXPECTED_FILES if not (tmp_path / name).is_file()]
    assert missing == []


def test_the_readme_reads_in_a_terminal(tmp_path: Path) -> None:
    """It is plain text, meant to be read on the server with ``less``.

    Eighty columns is the width that survives a terminal nobody widened, and this file
    is the one piece of documentation an operator reads where there is no browser. The
    check is here because nothing else looks at it: it is not Markdown, so the Markdown
    scan does not, and it ships, so a line that runs off the screen ships too.
    """
    scripts.write_scripts(tmp_path)
    readme = (tmp_path / 'README.txt').read_text(encoding='utf-8')

    too_wide = [line for line in readme.splitlines() if len(line) > 80]
    assert too_wide == []
    assert '\t' not in readme


def test_the_copy_is_the_packaged_file(tmp_path: Path) -> None:
    """Byte for byte, so a copy cannot be a stale or rewritten version of the chain."""
    written = scripts.write_scripts(tmp_path)
    reader = tmp_path / 'import_and_deploy' / '_read_deploy_env.sh'

    assert reader in written
    assert 'deploy.env' in reader.read_text(encoding='utf-8')


def test_shell_scripts_come_out_executable(tmp_path: Path) -> None:
    """A wheel does not carry the executable bit, so the command has to apply it.

    Without this the copy is a directory of files the operator has to chmod before the
    chain will run at all, and the first symptom is "permission denied" from a deploy.
    """
    scripts.write_scripts(tmp_path)

    deploy = tmp_path / 'import_and_deploy' / 'deploy_new_code_and_database.sh'
    template = tmp_path / 'deploy.env.template'
    assert os.access(deploy, os.X_OK)
    assert not stat.S_IMODE(template.stat().st_mode) & stat.S_IXUSR


def test_the_copy_records_the_release_it_came_from(tmp_path: Path) -> None:
    """The deploy scripts read this file and object when it is not the release being
    deployed, so a copy that carried no version could not be caught out of step."""
    written = scripts.write_scripts(tmp_path)
    stamp = tmp_path / scripts.VERSION_FILE

    assert stamp in written
    assert stamp.read_text(encoding='utf-8').strip() == importlib.metadata.version('rms-opus')


def test_the_version_is_rewritten_by_a_refresh(tmp_path: Path) -> None:
    """A refresh is what brings a copy up to the release being deployed, stamp included."""
    scripts.write_scripts(tmp_path)
    (tmp_path / scripts.VERSION_FILE).write_text('0.0.1\n', encoding='utf-8')

    scripts.write_scripts(tmp_path, force=True)

    assert (tmp_path / scripts.VERSION_FILE).read_text(encoding='utf-8').strip() != '0.0.1'


def test_a_refresh_replaces_files_rather_than_rewriting_them(tmp_path: Path) -> None:
    """The file at each path is a new one, which is what makes a refresh safe to run.

    ``update_deploy_scripts.sh`` refreshes the chain it is itself part of. Bash reads a
    script as it executes it and resumes at the offset it had reached, so a file
    truncated and filled again underneath it carries on inside the new text: measured,
    with a longer replacement, bash dies on a fragment of it. Renaming a new file over
    the old one leaves the running script's own file intact -- unlinked from the
    directory, still open, still read to its end -- so this is the property to hold, and
    a distinct inode is what says the rename happened.
    """
    scripts.write_scripts(tmp_path)
    script = tmp_path / 'import_and_deploy' / 'update_deploy_scripts.sh'
    before = script.stat().st_ino

    scripts.write_scripts(tmp_path, force=True)

    assert script.stat().st_ino != before
    assert os.access(script, os.X_OK)


def test_an_existing_copy_is_not_replaced(tmp_path: Path) -> None:
    """The operator's own edits, and the secrets beside them, are not this command's."""
    scripts.write_scripts(tmp_path)
    edited = tmp_path / 'deploy.env.template'
    edited.write_text('mine', encoding='utf-8')

    with pytest.raises(FileExistsError, match='already exists'):
        scripts.write_scripts(tmp_path)

    assert edited.read_text(encoding='utf-8') == 'mine'


def test_force_replaces_it(tmp_path: Path) -> None:
    """Which is how a copy is brought up to the version now installed."""
    scripts.write_scripts(tmp_path)
    edited = tmp_path / 'deploy.env.template'
    edited.write_text('mine', encoding='utf-8')

    scripts.write_scripts(tmp_path, force=True)

    assert edited.read_text(encoding='utf-8') != 'mine'
