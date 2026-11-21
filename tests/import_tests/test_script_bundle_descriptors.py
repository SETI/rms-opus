"""The bundles the integration import script lists, as the fixture builder reads them."""

from pathlib import Path

import pytest

from import_tests.tools import holdings_survey

#: The repository's integration import script.
_SCRIPT = Path(__file__).resolve().parents[2] / holdings_survey.INTEGRATION_SCRIPT


def test_the_array_gives_its_entries_in_order_without_its_comments(tmp_path: Path) -> None:
    """Several entries a line, a commented-out entry and a trailing comment."""
    script = tmp_path / 'import.sh'
    script.write_text(
        'echo before\n'
        'TEST_BUNDLES=(\n'
        '    A_1 A_2\n'
        '    B_1  # the B mission\n'
        '    # C_1\n'
        ')\n'
        'opus_import_all --sets "$(IFS=,; echo "${TEST_BUNDLES[*]}")"\n',
        encoding='utf-8',
    )
    assert holdings_survey.script_bundle_descriptors(script) == ['A_1', 'A_2', 'B_1']


def test_a_script_without_the_array_is_refused(tmp_path: Path) -> None:
    """No ``TEST_BUNDLES=(`` line is an error, not an empty list."""
    script = tmp_path / 'import.sh'
    script.write_text('opus_import_all --sets A_1\n', encoding='utf-8')
    with pytest.raises(ValueError, match='has no TEST_BUNDLES'):
        holdings_survey.script_bundle_descriptors(script)


def test_an_array_never_closed_is_refused(tmp_path: Path) -> None:
    """An array without its ``)`` line is an error, not the rest of the file."""
    script = tmp_path / 'import.sh'
    script.write_text('TEST_BUNDLES=(\n    A_1\n', encoding='utf-8')
    with pytest.raises(ValueError, match='not closed'):
        holdings_survey.script_bundle_descriptors(script)


def test_the_repository_script_lists_its_bundles() -> None:
    """The script's list is read, and the commented-out bundle is not in it."""
    descriptors = holdings_survey.script_bundle_descriptors(_SCRIPT)
    assert descriptors[0] == 'COISS_2002'
    assert 'cassini_iss_fring_mosaics_rsfrench2025' not in descriptors
    assert len(descriptors) == len(set(descriptors))
