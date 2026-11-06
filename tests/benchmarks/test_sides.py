"""The rule that spells each step of the measured sequence from a side's own help."""

import subprocess  # nosec B404 - the test builds a scratch git repository
import sys
from pathlib import Path

import pytest

from benchmarks.sides import Side, SideError, Spelling, listed_options, require_no_pythonpath
from opus_import import cli

#: Help text of a side from the harness's first commit's shape.
OLD_HELP = """
  --do-all-import   Perform all import functions
  --import          Perform an import
  --cleanup-aux-tables
  --drop-cache-tables
  --validate-perm   Perform validation
  --drop-permanent-tables  requires --scorched-earth
  --scorched-earth
  --timing-json PATH
"""

#: Help text of a side after every rename the plan names.
NEW_HELP = """
  --import          Import bundles into the permanent tables
  --finalize
  --reset-search-tables
  --validate
  --scorched-earth  Erase everything; needs --yes
  --yes
  --write-schema-version
  --timing-json PATH
"""


def test_an_option_is_listed_only_as_a_whole_token() -> None:
    """``--validate`` is not found inside ``--validate-perm``."""
    assert listed_options('  --validate-perm  check it') == frozenset({'--validate-perm'})


def test_an_option_followed_by_punctuation_is_listed() -> None:
    """A comma or a closing bracket ends a token as a space does."""
    assert listed_options('[--yes], --finalize.') == frozenset({'--yes', '--finalize'})


def test_a_side_with_the_first_commits_options_is_spelled_with_them() -> None:
    """Each fallback is chosen when the newer option is absent."""
    spelling = Spelling.from_help(OLD_HELP)
    assert spelling == Spelling(
        erase=('--drop-permanent-tables', '--scorched-earth'),
        bundle_import='--do-all-import',
        finalize='--cleanup-aux-tables',
        reset_search_tables='--drop-cache-tables',
        validate='--validate-perm',
        write_schema_version=(),
        timing_json='--timing-json',
        skipped_steps=('write_schema_version',),
    )


def test_a_side_with_the_renamed_options_is_spelled_with_them() -> None:
    """Each newer option is chosen once the side lists it."""
    spelling = Spelling.from_help(NEW_HELP)
    assert spelling == Spelling(
        erase=('--scorched-earth', '--yes'),
        bundle_import='--import',
        finalize='--finalize',
        reset_search_tables='--reset-search-tables',
        validate='--validate',
        write_schema_version=('--write-schema-version',),
        timing_json='--timing-json',
        skipped_steps=(),
    )


def test_a_side_without_timings_skips_them() -> None:
    """No ``--timing-json`` means no timing options and a named skipped step."""
    spelling = Spelling.from_help(OLD_HELP.replace('--timing-json PATH', ''))
    assert spelling.timing_args(Path('t.json')) == ()
    assert 'timing_json' in spelling.skipped_steps


def test_timing_options_name_the_file() -> None:
    """The option and the path go on the command line together."""
    assert Spelling.from_help(OLD_HELP).timing_args(Path('t.json')) == ('--timing-json', 't.json')


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('bundle_import', '--do-all-import'),
        ('finalize', '--cleanup-aux-tables'),
        ('reset_search_tables', '--drop-cache-tables'),
        ('validate', '--validate-perm'),
        ('erase', ('--drop-permanent-tables', '--scorched-earth')),
        ('timing_json', '--timing-json'),
    ],
)
def test_this_checkouts_own_help_is_spelled_as_expected(field: str, expected: object) -> None:
    """The rule applied to the import's real help gives the options this tree has."""
    spelling = Spelling.from_help(cli._create_argument_parser().format_help())
    assert getattr(spelling, field) == expected


@pytest.mark.parametrize(
    ('help_text', 'arguments', 'expected'),
    [
        (OLD_HELP, ['--drop-permanent-tables', '--scorched-earth'], 'erase'),
        (NEW_HELP, ['--scorched-earth', '--yes', '--timing-json', 't.json'], 'erase'),
        (
            OLD_HELP,
            ['--do-all-import', '--timing-json', 't.json', 'COISS_2002'],
            'bundle_import:COISS_2002',
        ),
        (NEW_HELP, ['--import', 'COISS_2002'], 'bundle_import:COISS_2002'),
        (OLD_HELP, ['--cleanup-aux-tables'], 'finalize'),
        (NEW_HELP, ['--finalize'], 'finalize'),
        (OLD_HELP, ['--import-dictionary'], 'import_dictionary'),
        (OLD_HELP, ['manage.py', 'migrate'], 'migrate'),
        (OLD_HELP, ['--validate-perm'], 'validate'),
        (NEW_HELP, ['--validate'], 'validate'),
        (NEW_HELP, ['--write-schema-version'], 'write_schema_version'),
        (OLD_HELP, ['--drop-cache-tables'], 'reset_search_tables'),
        (OLD_HELP, ['--update-mult-info', '--timing-json', 't.json'], '--update-mult-info'),
    ],
)
def test_an_invocation_is_named_by_its_role_on_either_side(
    help_text: str, arguments: list[str], expected: str
) -> None:
    """A step two sides spell differently gets one name, so their metrics line up."""
    assert Spelling.from_help(help_text).role(arguments) == expected


def _git(root: Path, *arguments: str) -> None:
    """Run git in a scratch repository, failing the test if it fails."""
    subprocess.run(  # nosec B603 B607 - git, with the test's own arguments
        ['git', '-C', str(root), *arguments],
        check=True,
        capture_output=True,
    )


@pytest.mark.parametrize(
    ('path', 'dirty'),
    [
        ('src/new_module.py', True),
        ('benchmarks/floors/uncommitted.json', False),
    ],
)
def test_only_an_untracked_file_under_src_makes_the_checkout_dirty(
    tmp_path: Path, path: str, dirty: bool
) -> None:
    """The editable install imports a new file under src/; a stray result changes nothing."""
    _git(tmp_path, 'init', '-q')
    (tmp_path / 'README').write_text('x\n')
    _git(tmp_path, 'add', 'README')
    _git(tmp_path, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x')
    side = Side(Path(sys.executable), tmp_path)
    assert side.environment()['git_dirty'] is False
    (tmp_path / path).parent.mkdir(parents=True)
    (tmp_path / path).write_text('x\n')
    assert side.environment()['git_dirty'] is dirty


def test_a_set_pythonpath_is_refused() -> None:
    """Both sides would import the checkout it names, whatever commit each records."""
    with pytest.raises(SideError, match='unset PYTHONPATH'):
        require_no_pythonpath({'PYTHONPATH': '/some/checkout/src'})
    require_no_pythonpath({'PYTHONPATH': ''})
    require_no_pythonpath({})
