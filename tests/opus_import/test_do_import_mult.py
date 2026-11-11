"""How the import finds, adds and reports the values of a mult field.

A stand-in database holds one field's stored rows, so the cache, the conflict warning,
the refusal of a value outside a pinned list and the id ceiling are driven without a
server. The field ids are given, as `opus_import.mult_fields.ensure_mult_fields` would
have read them.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from opus_import.context import ImportContext
from opus_import.importdb.super import ImportDBSuper
from opus_import.mult_fields import MultFieldInfo
from opus_import.steps import do_import_mult
from opus_import.steps.do_import_mult import MAX_MULT_ID, MultIdOverflowError

from .conftest import RecordingLogger, make_context

#: The stand-in column, discovered from the data.
COLUMN: dict[str, Any] = {'field_name': 'quality', 'pi_form_type': 'GROUP'}

#: The stand-in pinned column.
PINNED: dict[str, Any] = {
    'field_name': 'kind',
    'pi_form_type': 'GROUP',
    'mult_options': [[0, 'A', 'Alpha', 10, 'Y', None, None], [1, 'B', 'Beta', 20, 'Y', None, None]],
}


class _StoredRows:
    """A stand-in database whose ``mult`` holds the given rows for every field."""

    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self.rows = rows

    @staticmethod
    def quote_identifier(name: str) -> str:
        return f'`{name}`'

    def read_rows(self, table_name: str, *_args: Any) -> list[tuple[Any, ...]]:
        return self.rows if table_name == 'mult' else []


def _context(rows: list[tuple[Any, ...]] | None = None) -> ImportContext:
    """Return a context over stored `rows`: ``(id, value, label, pin, display, grouping)``."""
    ctx = make_context()
    ctx.args.suppress_mult_messages = True
    ctx.db = cast(ImportDBSuper, _StoredRows(rows or []))
    ctx.mult_fields = {
        'obs_x.quality': MultFieldInfo(1, pinned=False),
        'obs_x.kind': MultFieldInfo(2, pinned=True),
    }
    return ctx


def _update(ctx: ImportContext, column: dict[str, Any], value: Any, label: Any, **kw: Any) -> Any:
    """Resolve one value of the stand-in table ``obs_x``."""
    return do_import_mult.update_mult_table(
        ctx, 'obs_x', column['field_name'], column, value, label, **kw
    )


def _warnings(ctx: ImportContext) -> list[str]:
    return cast(RecordingLogger, ctx.logger).messages_at('warning')


def test_a_new_value_takes_the_id_after_the_highest() -> None:
    """Ids count on from the field's highest, the first being one above it."""
    ctx = _context([(4, 'GOOD', 'Good', None, 'Y', None)])

    assert _update(ctx, COLUMN, 'POOR', 'Poor') == 5
    assert _update(ctx, COLUMN, 'FAIR', 'Fair') == 6
    assert _update(ctx, COLUMN, 'POOR', 'Poor') == 5


def test_the_first_value_of_an_empty_field_is_id_zero() -> None:
    """A field with no rows starts at 0, as the observation columns hold today."""
    assert _update(_context(), COLUMN, 'X', 'X') == 0


def test_a_value_differing_only_in_case_finds_the_stored_row() -> None:
    """The cache compares as the server's collation does, as the unique key would."""
    ctx = _context([(3, 'FAIR', 'Fair', None, 'Y', None)])

    assert _update(ctx, COLUMN, 'fair', 'Fair') == 3
    assert ctx.mult_table_cache['obs_x.quality'].new_rows == []


def test_none_is_stored_as_the_empty_string() -> None:
    """The absent value is ``''``, so a unique key deduplicates it."""
    ctx = _context([(0, '', 'N/A', None, 'Y', None)])

    assert _update(ctx, COLUMN, None, 'N/A') == 0
    assert _update(ctx, COLUMN, '', 'N/A') == 0


def test_a_different_label_keeps_the_stored_row_and_warns_once() -> None:
    """The stored presentation stays; the warning names the field, value and labels."""
    ctx = _context([(3, 'GOOD', 'Good', None, 'Y', None)])

    assert _update(ctx, COLUMN, 'GOOD', 'Excellent') == 3
    assert _update(ctx, COLUMN, 'GOOD', 'Excellent') == 3

    (message,) = _warnings(ctx)
    assert '"obs_x.quality"' in message
    assert '"GOOD"' in message
    assert '"Good"' in message
    assert '"Excellent"' in message
    assert 'mult_overrides' in message
    assert ctx.mult_table_cache['obs_x.quality'].rows[0]['label'] == 'Good'


@pytest.mark.parametrize(
    ('kw', 'differs'),
    [({'disp': 'N'}, True), ({'grouping': 'G'}, True), ({}, False)],
    ids=['display', 'grouping', 'same'],
)
def test_a_different_display_or_grouping_warns_too(kw: dict[str, Any], differs: bool) -> None:
    ctx = _context([(3, 'GOOD', 'Good', None, 'Y', None)])

    _update(ctx, COLUMN, 'GOOD', 'Good', **kw)

    assert bool(_warnings(ctx)) is differs


def test_a_value_its_column_overrides_does_not_warn() -> None:
    """A renamed value's stored label differs from the computed one on purpose."""
    column = {**COLUMN, 'mult_overrides': [{'value': 'good', 'label': 'Excellent'}]}
    ctx = _context([(3, 'GOOD', 'Excellent', None, 'Y', None)])

    assert _update(ctx, column, 'GOOD', 'Good') == 3
    assert _warnings(ctx) == []


def test_a_pinned_field_serves_its_list_and_never_warns() -> None:
    """A pinned field's presentation is its list, whatever the obs class computes."""
    ctx = _context()

    assert _update(ctx, PINNED, 'B', 'Something else') == 1
    assert _warnings(ctx) == []


def test_a_value_outside_a_pinned_list_is_an_error_and_gets_the_absent_value() -> None:
    """The bundle fails; under ``--ignore-errors`` the row holds the absent value's id."""
    ctx = _context()

    first = _update(ctx, PINNED, 'Z', 'Zed')
    second = _update(ctx, PINNED, 'Y', 'Why')

    assert first == second == 2
    cache = ctx.mult_table_cache['obs_x.kind']
    assert cache.find('')['label'] == 'N/A'  # type: ignore[index]
    assert ctx.import_has_bad_data
    assert cast(RecordingLogger, ctx.logger).messages_at('error') == [
        'Unable to add value "Z" to preprogrammed mult field "obs_x.kind"',
        'Unable to add value "Y" to preprogrammed mult field "obs_x.kind"',
    ]


def test_a_value_outside_a_pinned_list_holding_the_absent_value_gets_its_id() -> None:
    column = {
        **PINNED,
        'mult_options': [*PINNED['mult_options'], [7, None, 'N/A', 30, 'Y', None, None]],
    }

    assert _update(_context(), column, 'Z', 'Zed') == 7


def test_an_id_above_the_type_s_maximum_is_refused_naming_the_field() -> None:
    """The import stops rather than write an id the column cannot hold."""
    ctx = _context([(MAX_MULT_ID, 'LAST', 'Last', None, 'Y', None)])

    with pytest.raises(MultIdOverflowError, match=r'"obs_x\.quality"'):
        _update(ctx, COLUMN, 'MORE', 'More')


def test_a_new_group_is_written_once_with_its_pin() -> None:
    """A group first met is added to ``mult_group``; one already there is not."""
    ctx = _context()

    _update(ctx, COLUMN, 'A', 'A', grouping='Saturn', group_pin=60)
    _update(ctx, COLUMN, 'B', 'B', grouping='saturn', group_pin=70)

    assert ctx.mult_table_cache['obs_x.quality'].new_groups == [
        {'field_id': 1, 'grouping': 'Saturn', 'group_pin': 60}
    ]


def test_a_lookup_finds_a_value_without_adding_it() -> None:
    ctx = _context([(3, 'FAIR', 'Fair', None, 'Y', None)])

    assert do_import_mult.mult_table_lookup_id(ctx, 'obs_x', 'quality', COLUMN, 'fair') == 3
    assert do_import_mult.mult_table_lookup_id(ctx, 'obs_x', 'quality', COLUMN, 'X') is None
    assert ctx.modified_mult_tables == set()
