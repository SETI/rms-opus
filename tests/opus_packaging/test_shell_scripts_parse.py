"""Tests that every shell script in the repository parses.

This exists because a syntax error in a shell script is invisible until the script
runs, and some of these scripts run only on a production server. ``_opus_import_
volumes.sh`` carried one for months: a ``#`` comment placed inside a backslash-continued
list ends the continuation, so ``bash -n`` failed, and ``_run_full_opus_import.sh`` --
which sources it -- aborted before importing a single bundle. Nothing in CI noticed,
because nothing in CI ran it. It is still broken on ``main``.

Two families are checked:

* every shell file in the tree, found by rule rather than by a list;
* every ``run:`` block in every GitHub Actions workflow, extracted from the parsed YAML.
  A heredoc terminator left indented inside a YAML block scalar produces shell that does
  not parse, and nothing reports that until the job runs.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

# Directories that hold no shell script of ours: build output, virtual environments,
# git internals, and the working documents for the modernization.
SKIP_DIRECTORIES = {'.git', 'venv', '.venv', 'opus_venv', '_build', 'node_modules', '__pycache__'}

# GitHub Actions expression syntax is not shell; bash cannot parse `${{ ... }}`.
GHA_EXPRESSION = re.compile(r'\$\{\{[^}]*\}\}')

pytestmark = pytest.mark.skipif(
    os.name != 'posix', reason='bash is what these scripts are written for'
)


def _shell_files() -> list[Path]:
    """Every shell file in the tree, by rule: the suffix, or a shell shebang.

    A rule rather than a list, so a script added later is covered without anyone
    remembering to add it here -- which is the failure that let the broken one live.
    """
    found: list[Path] = []
    for path in REPO_ROOT.rglob('*'):
        if any(part in SKIP_DIRECTORIES for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix in {'.sh'} or path.name.endswith('.sh_template'):
            found.append(path)
            continue
        # An extensionless script is still a script.
        if path.suffix == '':
            try:
                with path.open('rb') as handle:
                    first = handle.readline(128)
            except OSError:  # pragma: no cover - unreadable file
                continue
            if first.startswith(b'#!') and (b'sh' in first):
                found.append(path)
    return sorted(found)


def _workflow_run_blocks() -> list[tuple[str, str]]:
    """Every ``run:`` block in every workflow, as ``(label, script)``."""
    blocks: list[tuple[str, str]] = []
    for workflow in sorted((REPO_ROOT / '.github' / 'workflows').glob('*.yml')):
        data = yaml.safe_load(workflow.read_text())
        for job_id, job in data['jobs'].items():
            for index, step in enumerate(job.get('steps', [])):
                script = step.get('run')
                if script:
                    name = step.get('name', f'step {index}')
                    blocks.append((f'{workflow.name}:{job_id}:{name}', script))
    return blocks


def test_some_shell_files_were_found() -> None:
    """The discovery rule finds something.

    Without this, a rule that silently matched nothing would make every test below
    vacuously pass -- the shape this whole module exists to catch.
    """
    found = _shell_files()
    assert len(found) > 20, [str(p) for p in found]
    names = {p.name for p in found}
    assert 'run-all-checks.sh' in names
    assert '_opus_import_volumes.sh' in names


def _parse(script: str | None = None, path: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run ``bash -n`` over a file or a string."""
    if path is not None:
        return subprocess.run(
            ['bash', '-n', str(path)], capture_output=True, text=True, check=False
        )
    return subprocess.run(
        ['bash', '-n'], input=script, capture_output=True, text=True, check=False
    )


def _assert_parses(result: subprocess.CompletedProcess[str], label: str) -> None:
    """Fail unless ``bash -n`` was both successful *and* silent.

    The exit status alone is not enough, and assuming it was would have made this whole
    module a check that cannot fail. ``bash -n`` **exits 0** on an unterminated
    heredoc -- the exact defect the workflow half of this module exists to catch -- and
    reports it only as ``warning: here-document at line N delimited by end-of-file``
    on stderr. A clean parse writes nothing, so silence is the real signal.
    """
    assert result.returncode == 0, f'{label}\n{result.stderr}'
    assert result.stderr == '', f'{label}\n{result.stderr}'


@pytest.mark.parametrize('script', _shell_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_shell_file_parses(script: Path) -> None:
    """``bash -n`` accepts the file, and says nothing while doing so."""
    _assert_parses(_parse(path=script), str(script))


def test_the_parse_check_can_actually_fail(tmp_path: Path) -> None:
    """A file with a syntax error is rejected.

    Constructed with the exact defect this module was written for: a ``#`` comment
    inside a backslash continuation, which reads as harmless and is not.
    """
    broken = tmp_path / 'broken.sh'
    broken.write_text('for V in \\\n  a \\\n# disabled\n  b \\\n  c\ndo\n  echo $V\ndone\n')
    result = _parse(path=broken)
    assert result.returncode != 0, 'bash -n accepted a comment inside a continuation'


def test_an_unterminated_heredoc_is_caught_despite_a_zero_exit_status(tmp_path: Path) -> None:
    """The other constructed failure, and the reason this module checks stderr.

    An indented heredoc terminator inside a YAML block scalar is the way a workflow step
    breaks, and ``bash -n`` returns **0** for it. Without the stderr assertion the
    workflow tests below would agree with any indentation.
    """
    broken = tmp_path / 'unterminated.sh'
    broken.write_text("python3 - <<'PY'\nprint(1)\n  PY\n")
    result = _parse(path=broken)
    assert result.returncode == 0, 'bash -n started failing on this; update the reasoning'
    assert 'delimited by end-of-file' in result.stderr
    with pytest.raises(AssertionError):
        _assert_parses(result, str(broken))


def test_some_workflow_run_blocks_were_found() -> None:
    """The workflow extraction finds something, for the same reason as above."""
    blocks = _workflow_run_blocks()
    assert len(blocks) > 10, [label for label, _ in blocks]


@pytest.mark.parametrize(
    ('label', 'script'), _workflow_run_blocks(), ids=[label for label, _ in _workflow_run_blocks()]
)
def test_workflow_run_block_parses(label: str, script: str) -> None:
    """The shell inside each workflow step parses once expressions are substituted."""
    _assert_parses(_parse(script=GHA_EXPRESSION.sub('PLACEHOLDER', script)), label)
