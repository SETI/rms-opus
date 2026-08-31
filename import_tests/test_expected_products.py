"""The expected-products assertion: what the recorder saw is what the import stored.

This is the load-bearing test of the suite, because a shelf gap fails silently rather
than loudly. A shelf file that is missing makes the product skipped with a warning; a key
missing from a shelf that is present makes ``os_path_exists`` return False with no
warning at all, so the candidate simply never existed and the import is quietly smaller.
Nothing about the run's exit status, its logs or its row counts would show it.

Comparing both directions against the products recorded from the real holdings is what
turns that into a red test.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from import_tests.tools import expected_products, fixture_layout, holdings_survey

if TYPE_CHECKING:
    from import_tests.tools.build_run import ImportRun
    from import_tests.tools.golden_io import DatabaseCredentials


@pytest.fixture(scope='session')
def product_sets(
    main_run: ImportRun, db_credentials: DatabaseCredentials
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Return the recorded products and the imported ones, both keyed by bundle."""
    return (
        expected_products.read_expected_products(),
        expected_products.read_obs_files(db_credentials, main_run.schema),
    )


def _exclusions() -> dict[str, str]:
    """Return the excluded instrument classes and the reason each one gives.

    Returns:
        The class name mapped to its reason, for every non-comment, non-blank line.

    Raises:
        ValueError: If a line names a class without a reason. The exclusions file is a
            whitelist like the other two, and an entry nobody justified is what a
            whitelist exists to prevent.
    """
    excluded = {}
    for number, line in enumerate(
        fixture_layout.EXCLUSIONS_FILE.read_text(encoding='utf-8').splitlines(), start=1
    ):
        stripped = line.strip()
        if len(stripped) == 0 or stripped.startswith('#'):
            continue
        name, tab, reason = line.partition('\t')
        if len(tab) == 0 or len(reason.strip()) == 0:
            raise ValueError(f'{fixture_layout.EXCLUSIONS_FILE.name} line {number} gives no reason')
        excluded[name.strip()] = reason.strip()
    return excluded


def test_every_registered_type_is_covered(main_run: ImportRun) -> None:
    """Every bundle type OPUS imports is represented, or excluded with a reason.

    The completeness check is the registry minus the exclusions, so a newly registered
    type arrives here as a failure rather than as coverage nobody noticed was missing.
    """
    entries = holdings_survey.registry_entries()
    covered = {
        entry.instrument_class_name
        for entry in entries
        if any(re.fullmatch(entry.pattern, bundle) for bundle in main_run.bundles)
    }
    assert covered == {entry.instrument_class_name for entry in entries} - set(_exclusions())


def test_every_exclusion_names_a_registered_type() -> None:
    """No exclusion names a class the registry does not carry.

    An exclusion for a class nobody registers any more excuses nothing, and would go on
    excusing whatever type later took its name.
    """
    registered = {entry.instrument_class_name for entry in holdings_survey.registry_entries()}
    assert sorted(set(_exclusions()) - registered) == []


def test_fixture_records_products_for_every_bundle(main_run: ImportRun) -> None:
    """Every bundle the fixture imports has an expected-products file to be held to."""
    assert set(main_run.bundles) == set(expected_products.read_expected_products())


def test_every_recorded_product_was_imported(
    product_sets: tuple[dict[str, set[str]], dict[str, set[str]]],
) -> None:
    """No product the real holdings hold is missing from ``obs_files``.

    A missing one means a shelf manifest lost a key, which produces no error and no
    warning anywhere else in the run.
    """
    missing, _extra = expected_products.differences(*product_sets)
    assert missing == {}


def test_no_unrecorded_product_was_imported(
    product_sets: tuple[dict[str, set[str]], dict[str, set[str]]],
) -> None:
    """No ``obs_files`` row names a product the recorder did not see.

    An extra one means the fixture grew a product family the recording does not cover --
    a versioned tree, or a documents path -- which the goldens would then bless.
    """
    _missing, extra = expected_products.differences(*product_sets)
    assert extra == {}
