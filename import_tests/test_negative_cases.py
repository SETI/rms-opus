"""The cases that must go wrong, and the behavior that is right when they do.

Each of these is its own run into its own schema with its own log directory -- pdslogger
appends, so a shared log directory would put a deliberately broken run's errors in front
of the clean run's assertions -- and each is exempt from the main run's clean-log rules.

A negative run stops after its imports rather than following the main run's full
sequence. Everything asserted here is in place by then: ``--do-all-import`` copies to the
permanent tables, so ``obs_general`` and the target-name mult table are written, and the
rest of what these tests read is the run's own step statuses and error log. The auxiliary
tables, the dictionary, the Django migration and the validation produce nothing any
assertion below looks at, and running them three times a suite bought only wall clock.
The main run keeps the production order, which is where that order is under test.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from import_tests.tools import fixture_layout, golden_io, negative_cases, run_logs

if TYPE_CHECKING:
    from pathlib import Path

    from import_tests.tools.build_run import ImportRun
    from import_tests.tools.golden_io import DatabaseCredentials

#: The table whose row is the observation, and the mult table its target name indexes.
_OBS_GENERAL = 'obs_general'
_TARGET_NAME_MULT = 'mult_obs_general_target_name'

#: The value an unknown target name falls back to under ``--import-ignore-errors``.
_OTHER_TARGET = 'OTHER'


def _row_count(credentials: DatabaseCredentials, schema: str, bundle: str) -> int:
    """Return how many observations one bundle contributed to a schema.

    Parameters:
        credentials: How to reach the database server.
        schema: The schema to count in.
        bundle: The bundle id.

    Returns:
        The ``obs_general`` row count for that bundle.
    """
    rows = golden_io.query(
        credentials,
        schema,
        f'SELECT COUNT(*) FROM `{_OBS_GENERAL}` WHERE bundle_id = %s',
        [bundle],
    )
    return int(rows[0][0])


def metadata_less_bundles() -> list[str]:
    """Return the fixture's volumes that have no metadata directory at all.

    Their primary index lives inside the volume instead, and every summary the import
    would otherwise merge in is simply absent -- which is the missing-metadata branch,
    reached by the volume set naturally rather than by a special case.

    Returns:
        The bundle ids, sorted.
    """
    with_metadata = _bundle_names(fixture_layout.PDS3_METADATA)
    in_volume = _bundle_names(fixture_layout.PDS3_VOLUME_INDEX)
    return sorted(in_volume - with_metadata)


def _bundle_names(root: Path) -> set[str]:
    """Return the bundle directory names two levels below a fixture root.

    Parameters:
        root: A fixture directory holding ``<bundle set>/<bundle>/`` trees.

    Returns:
        The bundle names, empty when the root does not exist.
    """
    if not root.is_dir():
        return set()
    return {
        bundle_dir.name
        for bundleset_dir in root.iterdir()
        if bundleset_dir.is_dir()
        for bundle_dir in bundleset_dir.iterdir()
        if bundle_dir.is_dir()
    }


def test_the_fixture_has_a_metadata_less_volume() -> None:
    """At least one fixture volume reaches the missing-metadata branch.

    Without one the branch is untested and nothing says so, because a volume that has
    its summaries produces no evidence that the code handling their absence works.
    """
    assert metadata_less_bundles() != []


@pytest.mark.parametrize('bundle', metadata_less_bundles())
def test_metadata_less_volume_still_imports(
    bundle: str, main_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """A volume with no summary files imports its observations anyway."""
    assert _row_count(db_credentials, main_run.schema, bundle) > 0


def test_duplicate_opus_ids_are_resolved_rather_than_rejected(
    duplicate_id_run: ImportRun,
) -> None:
    """Importing a volume twice in one invocation runs to the end without an error.

    That is the failure mode the flag prevents, and asking the finished database how
    many rows share an OPUS id would not see it: ``obs_general.opus_id`` carries a
    ``unique`` key, so a duplicate row cannot exist to be counted -- the *insert* is what
    fails. The flag makes the import delete each OPUS id's earlier row before writing the
    new one; without it, the second copy's insert is rejected and the run logs an error.
    """
    stopped = [
        f'{" ".join(step.arguments)} exited {step.returncode}' for step in duplicate_id_run.steps
    ]
    assert [line for line in stopped if not line.endswith('exited 0')] == []
    assert run_logs.distinct(run_logs.read_messages(duplicate_id_run.paths.errors_log)) == []


def test_duplicate_id_run_imported_the_observations(
    duplicate_id_run: ImportRun, main_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """Resolving the duplicates kept every observation rather than dropping any."""
    bundle = negative_cases.bundle_for_class(negative_cases.DUPLICATE_ID_INSTRUMENT_CLASS)
    duplicated = _row_count(db_credentials, duplicate_id_run.schema, bundle)
    clean = _row_count(db_credentials, main_run.schema, bundle)
    assert duplicated == clean


def test_unknown_target_is_reported(ignore_errors_run: ImportRun) -> None:
    """The crafted target name is reported, at error level, even though the run goes on."""
    recipe = negative_cases.load_recipe(negative_cases.IGNORE_ERRORS_CASE)
    assert recipe.value is not None
    messages = run_logs.read_messages(ignore_errors_run.paths.errors_log)
    assert any(recipe.value in message for message in messages), messages


def test_unknown_target_becomes_other(
    ignore_errors_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """An unknown target name imports as ``OTHER`` instead of dropping the observation.

    The flag has to reach the obs layer for the fallback to run at all, which is what
    this asserts: an ``OTHER`` row in the target-name mult table is the only evidence
    anywhere that the observation was kept rather than dropped.
    """
    rows = golden_io.query(
        db_credentials,
        ignore_errors_run.schema,
        f'SELECT value FROM `{_TARGET_NAME_MULT}`',
    )
    values = {str(row[0]).upper() for row in rows}
    assert _OTHER_TARGET in values, sorted(values)


def test_unknown_target_observation_is_not_dropped(
    ignore_errors_run: ImportRun, main_run: ImportRun, db_credentials: DatabaseCredentials
) -> None:
    """The perturbed volume imports as many observations as the unperturbed one."""
    recipe = negative_cases.load_recipe(negative_cases.IGNORE_ERRORS_CASE)
    perturbed = _row_count(db_credentials, ignore_errors_run.schema, recipe.bundle)
    clean = _row_count(db_credentials, main_run.schema, recipe.bundle)
    assert perturbed == clean
