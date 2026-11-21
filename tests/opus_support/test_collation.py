"""The key `opus_support.collation_key` folds a string to, as the server compares it."""

import pytest

from opus_support import collation_key


@pytest.mark.parametrize(
    ('first', 'second'),
    [('Saturn', 'saturn'), ('Saturn', 'SATURN'), ('Jupiter', 'Jupitér'), ('Straße', 'STRASSE')],
    ids=['lower', 'upper', 'accent', 'sharp-s'],
)
def test__collation_key_ignores_case_and_accents(first: str, second: str) -> None:
    assert collation_key(first) == collation_key(second)


@pytest.mark.parametrize(
    ('first', 'second'),
    [('Saturn', 'Saturn '), ('Saturn', 'Saturns'), ('N/A', 'NA')],
    ids=['trailing-space', 'plural', 'punctuation'],
)
def test__collation_key_keeps_what_the_server_compares(first: str, second: str) -> None:
    assert collation_key(first) != collation_key(second)
