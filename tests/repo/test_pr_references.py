"""No shipped file may name one of the modernization plan's own pull requests.

The plan numbers its pull requests, and for a while that numbering leaked into the
tree: configuration comments, docstrings, shell scripts and workflow YAML all justified
themselves by naming the pull request that had done the work, or the one that was going
to. **Nothing in a checkout can resolve such a reference.** The plan lives in one
Markdown file, the numbers in it are not GitHub numbers, and a reader who finds one in a
comment has no way to turn it into a fact. The comment has to state what is true and why
instead -- which is also more durable, because it survives the plan.

The rule decayed the first time precisely because nothing enforced it, so this is the
enforcement. It is a text scan over every file git tracks, minus the few places where
naming a pull request is the correct thing to do.

The pattern is anchored on word boundaries, and that is load-bearing rather than
tidiness: the packaged PDS data dictionary is full of dataset identifiers whose
instrument code is ``PPR``, and an unanchored pattern matches inside every one of them.
``test_the_pattern_ignores_a_pds_dataset_identifier`` is what keeps that anchoring from
being removed as redundant.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The two letters, a hyphen, the number, and the optional letter an inserted pull
#: request carries. Case-insensitive, because a lower-case spelling refers to the same
#: unresolvable thing. Matched against bytes so that no file has to decode.
PLAN_PR_REFERENCE = re.compile(rb'\bPR-[0-9]+[a-z]?\b', re.IGNORECASE)

#: Where naming a pull request is correct, and therefore not scanned. `plans/` is the
#: plan itself and its Execution notes; `critiques/` holds the reviews of it; CLAUDE.md
#: is the executor's briefing, whose whole subject is which pull request to run. Every
#: one of them is a document *about* the sequence rather than a file the software ships.
UNSCANNED = ('plans/', 'critiques/', 'CLAUDE.md')


def _tracked_files() -> list[str]:
    """Return every path git tracks, relative to the repository root.

    Tracked rather than walked: that is exactly the set the repository ships, so a
    build directory, a virtual environment or an untracked scratch file cannot make
    this test either fail or pass. `check=True` because a scan that silently examined
    nothing would report a clean tree.

    Returns:
        The paths, in git's order.
    """
    finished = subprocess.run(['git', 'ls-files', '-z'], cwd=REPO_ROOT,
                              capture_output=True, check=True)
    return [name.decode() for name in finished.stdout.split(b'\0') if name]


def _scanned_files() -> list[str]:
    """Return the tracked paths this rule applies to.

    Returns:
        Every tracked path outside `UNSCANNED`.
    """
    return [name for name in _tracked_files() if not name.startswith(UNSCANNED)]


def _references_in(text: bytes, name: str) -> list[str]:
    """Return one report line per plan pull-request reference in `text`.

    Parameters:
        text: The file's bytes.
        name: The path to name in each report line.

    Returns:
        ``path:line: reference`` for each match, oldest first.
    """
    found = []
    for number, line in enumerate(text.split(b'\n'), start=1):
        for match in PLAN_PR_REFERENCE.finditer(line):
            found.append(f'{name}:{number}: {match.group().decode(errors="replace")}')
    return found


def test_the_scan_reaches_every_kind_of_file_it_has_to() -> None:
    """The enumeration is not empty and not narrowed to one corner of the tree.

    A scan that reached nothing would pass this module's gate for the wrong reason and
    go on doing so forever. The assertions below are canaries rather than an inventory:
    one file from each family that has carried a reference -- workflow YAML, a shell
    script, the project configuration, installed source, a test module, the developer
    guide, and the whitelist at the repository root that sits outside every tool's
    configured scope.
    """
    scanned = set(_scanned_files())

    assert len(scanned) > 500, len(scanned)
    for canary in (
        '.github/workflows/run-tests.yml',
        'scripts/run-all-checks.sh',
        'pyproject.toml',
        'src/opus_import/importdb/mysql.py',
        'tests/opus_import/test_cli.py',
        'docs/dev_guide_deployment.rst',
        'vulture_whitelist.py',
    ):
        assert canary in scanned, canary


def test_no_shipped_file_names_a_plan_pull_request() -> None:
    """The gate. State what is true and why, not which pull request did it."""
    found: list[str] = []
    for name in _scanned_files():
        path = REPO_ROOT / name
        if not path.is_file():  # a submodule or a broken symlink
            continue
        found.extend(_references_in(path.read_bytes(), name))

    assert found == [], (
        'These lines name a pull request from the modernization plan, which nothing in '
        'a checkout can resolve. Say what is true and why instead:\n' + '\n'.join(found)
    )


def test_the_scan_finds_a_reference_planted_in_a_file(tmp_path: Path) -> None:
    """The detector fires on a comment that names a pull request.

    Without this the gate above would be indistinguishable from a pattern that matches
    nothing at all, which is the shape a scan fails in: it goes green either way.

    The reference is assembled from pieces rather than written out, because this file is
    one of the files the gate scans and a literal one here would make the suite fail on
    itself. Do not "simplify" the concatenation away.
    """
    reference = 'PR' + '-07'
    planted = tmp_path / 'planted.toml'
    planted.write_text(f'# Retired by {reference}, which owned that tree.\n')

    found = _references_in(planted.read_bytes(), 'planted.toml')

    assert found == [f'planted.toml:1: {reference}']


def test_the_scan_finds_the_lower_case_and_suffixed_spellings(tmp_path: Path) -> None:
    """A lower-case reference and an inserted pull request's letter suffix both count.

    Both spellings occur in the plan, and both are equally unresolvable from a checkout;
    a pattern that missed either would leave the obvious way around the gate open.
    """
    planted = tmp_path / 'planted.py'
    planted.write_text('# ' + 'pr' + '-12 and ' + 'PR' + '-03a both.\n')

    found = _references_in(planted.read_bytes(), 'planted.py')

    assert len(found) == 2, found


def test_the_pattern_ignores_a_pds_dataset_identifier() -> None:
    """A PDS dataset id whose instrument code is ``PPR`` is not a reference.

    ``src/opus_import/dictionary_data/pdsdd.full`` ships dozens of these. Drop the
    leading word boundary from the pattern and every one of them matches, so the gate
    goes red on a tree that is clean -- and the natural repair is to stop scanning the
    packaged data, which would also stop scanning a file somebody might comment.
    """
    assert _references_in(b'"GO-A-PPR-2-EDR-GASPRA-V1.0",\n', 'pdsdd.full') == []


def test_the_unscanned_paths_are_carrying_something() -> None:
    """The exclusions are load-bearing, so removing one has to change the result.

    An exclusion list that excluded nothing would be indistinguishable from no list at
    all, and the next reader would delete it. This shows the plan really does hold the
    references the rule is about -- which is also why it is not scanned.
    """
    excluded = [name for name in _tracked_files() if name.startswith(UNSCANNED)]
    assert excluded, UNSCANNED

    hits = 0
    for name in excluded:
        path = REPO_ROOT / name
        if path.is_file():
            hits += len(_references_in(path.read_bytes(), name))
    assert hits > 100, hits


@pytest.mark.parametrize('prefix', UNSCANNED)
def test_each_unscanned_path_still_exists(prefix: str) -> None:
    """Each exclusion names something git tracks.

    A stale entry silences a directory that was renamed, and nothing else would notice.

    Parameters:
        prefix: The path prefix under test.
    """
    assert any(name.startswith(prefix) for name in _tracked_files()), prefix
