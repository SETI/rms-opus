"""Read the recorded product set, and compare it with what a run actually stored.

Both sides of the expected-products assertion live here so that the test and the golden
generator hold a run to the same standard: the generator refuses to bless a run this
comparison fails, and the test fails a run that stops satisfying it later.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from import_tests.tools import fixture_layout, golden_io
from import_tests.tools.bundle_recorder import ROOT_NAME_FOR_VERSION

if TYPE_CHECKING:
    from import_tests.tools.golden_io import DatabaseCredentials

#: The extension an expected-products file carries.
PRODUCTS_EXT = '.tsv'


def read_expected_products() -> dict[str, set[str]]:
    """Return the products the recorder saw, keyed by bundle.

    Returns:
        The root-prefixed paths each bundle's observations name.

    Raises:
        ValueError: If a line of an expected-products file is not a path and a size.
    """
    per_bundle: dict[str, set[str]] = {}
    for path in sorted(fixture_layout.EXPECTED_PRODUCTS_DIR.glob(f'*{PRODUCTS_EXT}')):
        paths: set[str] = set()
        for line in path.read_text(encoding='utf-8').splitlines():
            if len(line.strip()) == 0:
                continue
            product, tab, _size = line.partition('\t')
            if len(tab) == 0:
                raise ValueError(f'{path.name} has a line with no size: {line!r}')
            paths.add(product)
        per_bundle[path.stem] = paths
    return per_bundle


def read_obs_files(credentials: DatabaseCredentials, schema: str) -> dict[str, set[str]]:
    """Return the product files one run stored, keyed by bundle.

    ``obs_files`` holds a logical path, which has no holdings root on the front, so each
    row's regime root is prepended before it is compared with a recorded product.

    Parameters:
        credentials: How to reach the database server.
        schema: The schema the run imported into.

    Returns:
        The root-prefixed paths each bundle's rows name.
    """
    rows = golden_io.query(
        credentials, schema, 'SELECT bundle_id, pds_version, logical_path FROM obs_files'
    )
    per_bundle: dict[str, set[str]] = {}
    for bundle_id, pds_version, logical_path in rows:
        root = ROOT_NAME_FOR_VERSION[int(pds_version)]
        per_bundle.setdefault(str(bundle_id), set()).add(f'{root}/{logical_path}')
    return per_bundle


def differences(
    expected: dict[str, set[str]], actual: dict[str, set[str]]
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Compare the two product sets in both directions.

    Parameters:
        expected: What the recorder saw, keyed by bundle.
        actual: What the run stored, keyed by bundle.

    Returns:
        The recorded products no row names, and the rows no recording covers, each keyed
        by bundle and each holding only the bundles that differ.
    """
    missing = {
        bundle: sorted(paths - actual.get(bundle, set()))
        for bundle, paths in expected.items()
        if len(paths - actual.get(bundle, set())) > 0
    }
    extra = {
        bundle: sorted(paths - expected.get(bundle, set()))
        for bundle, paths in actual.items()
        if len(paths - expected.get(bundle, set())) > 0
    }
    return missing, extra
