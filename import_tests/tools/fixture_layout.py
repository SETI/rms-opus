"""Where everything the mini-holdings suite reads and writes lives.

One module holds the layout so that the recorder, the builder, the golden generator and
the tests all name the same directories. Nothing here reads a file; it only says where
the files are.
"""

from __future__ import annotations

from pathlib import Path

#: The repository root, three levels above this file (``import_tests/tools/``).
REPO_ROOT = Path(__file__).resolve().parents[2]

#: The recorded fixture: real subsetted metadata, shelf manifests, expected products.
#: It sits under ``tests/`` because it is holdings data rather than a test artifact.
FIXTURE_ROOT = REPO_ROOT / 'tests' / 'fixtures' / 'mini_holdings'

#: The suite's own artifacts, which the tests rather than the holdings own.
SUITE_ROOT = REPO_ROOT / 'import_tests'
GOLDENS_DIR = SUITE_ROOT / 'goldens'
SUITE_FIXTURES_DIR = SUITE_ROOT / 'fixtures'
NEGATIVE_DIR = SUITE_FIXTURES_DIR / 'negative'
UNEXECUTED_METHODS_FILE = SUITE_FIXTURES_DIR / 'unexecuted_methods.txt'

#: The two regime subtrees of the fixture, and what each holds.
PDS3_FIXTURE = FIXTURE_ROOT / 'pds3'
PDS4_FIXTURE = FIXTURE_ROOT / 'pds4'
PDS3_METADATA = PDS3_FIXTURE / 'metadata'
PDS4_METADATA = PDS4_FIXTURE / 'metadata'
PDS3_VOLINFO = PDS3_FIXTURE / '_volinfo'
PDS3_VOLUME_INDEX = PDS3_FIXTURE / 'volume_index'
PDS3_MANIFESTS = PDS3_FIXTURE / 'shelf_manifests'
PDS4_MANIFESTS = PDS4_FIXTURE / 'shelf_manifests'

#: Recorded reality the tests assert against.
EXPECTED_PRODUCTS_DIR = FIXTURE_ROOT / 'expected_products'
EXCLUSIONS_FILE = FIXTURE_ROOT / 'exclusions.tsv'
WARNING_WHITELIST_FILE = FIXTURE_ROOT / 'warning_whitelist.txt'

#: The directory names the built holdings roots must have. pdsfile finds a category
#: directory by string-replacing the holdings directory's own name, so these are not
#: free choices.
PDS3_ROOT_NAME = 'holdings'
PDS4_ROOT_NAME = 'pds4-holdings'

#: The in-volume index directory PDS3 bundles whose primary index is not under
#: ``metadata/`` keep their index in. The import reaches it with a plain
#: ``os.path.exists``, so it is materialized on disk rather than answered by a shelf.
VOLUME_INDEX_DIRNAME = 'INDEX'

#: Where the built PDS3 tree puts a volume's own index directory.
PDS3_VOLUMES_DIRNAME = 'volumes'

#: The schema every run of the suite imports into, with the pytest session's process id
#: appended. A negative case appends its own suffix after that. The process id is what
#: keeps two worktrees running against one MySQL server apart; a user name cannot.
SCHEMA_PREFIX = 'opus_import_test_'


def schema_name(pid: int, case: str | None = None) -> str:
    """Return the database schema one run of the suite imports into.

    Parameters:
        pid: The process id of the pytest session, or of the golden generator.
        case: The negative case's name, or None for the main run.

    Returns:
        The schema name, which always starts with `SCHEMA_PREFIX` so that a schema left
        behind by a run killed too hard for its finalizer is recognizable.
    """
    if case is None:
        return f'{SCHEMA_PREFIX}{pid}'
    return f'{SCHEMA_PREFIX}{pid}_{case}'
