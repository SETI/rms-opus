"""Static checks of the packaged table schemas, as documents, with no database.

The import reads each schema only where a code path happens to touch it, so a misspelled
key, a type ``create_table`` cannot render or a tooltip with no definition would surface
late, deep inside an import, or never. These tests read every file whole and check what
the import and the web application assume of it.

An entry is one of four kinds, told apart by its keys:

* a **column**, which has ``field_name``;
* a **link**, which has ``pi_referred_slug``: a ``param_info`` row for a column another
  table defines;
* a **definition**, which has ``definition`` and no ``field_name``: a dictionary term with
  no column of its own;
* a **table-level entry**, which has none of those: ``{"constraint": "..."}``, appended to
  ``CREATE TABLE`` as written; ``{"foreign_key": {...}}``, a foreign key with its
  columns, what it references, and optionally what deleting a referenced row does; or
  ``{"primary_key": [...]}``, ``{"unique": [...]}`` or ``{"key": [...]}``, a key over the
  listed columns.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

import opus_support
from opus_import import import_util, list_junctions, mult_fields
from opus_import.importdb.mysql import (
    MYSQL_CHARSET_SQL,
    MYSQL_ENUM_FIELD_TYPE,
    MYSQL_FIELD_TYPE_SQL,
    is_renderable_field_type,
    takes_charset,
)
from opus_import.steps.do_import_mult import PINNED_ABSENT_ID
from opus_import.table_keys import ON_DELETE_VALUES, TABLE_LEVEL_KEY_KINDS

#: The packaged schema directory, as a path.
_SCHEMA_DIR = Path(str(import_util.TABLE_SCHEMA_DIR))

#: The JSON files there that are not lists of entries.
_NOT_ENTRY_LISTS = {'param_info_ranges.json'}

#: Every key a column may carry: the ones some code reads, and the notes.
_COLUMN_KEYS = {
    # Defining the column.
    'field_name',
    'field_type',
    'field_key',
    'field_key_foreign',
    'field_notnull',
    'field_default',
    'field_autoincrement',
    'field_enum_options',
    'field_charset',
    # Filling and validating it.
    'data_source',
    'val_min',
    'val_max',
    'val_sentinel',
    'val_set_invalid_to_null',
    'mult_options',
    'mult_overrides',
    'mult_field',
    # Describing it to the user interface.
    'pi_category_name',
    'pi_disp_order',
    'pi_display',
    'pi_display_results',
    'pi_field_hints1',
    'pi_field_hints2',
    'pi_form_type',
    'pi_intro',
    'pi_label',
    'pi_label_results',
    'pi_old_slug',
    'pi_ranges',
    'pi_slug',
    'pi_sub_heading',
    'pi_tooltip',
    # Its tooltip.
    'definition',
    'definition_results',
    'pi_dict_context',
    'pi_dict_name',
    'pi_dict_context_results',
    'pi_dict_name_results',
    # Notes to the reader, which nothing consumes.
    'comment',
    'comments',
}

#: What every column has.
_COLUMN_REQUIRED = {'field_name', 'field_type'}

#: What a column with a ``param_info`` row has: the keys the ``param_info`` step reads
#: without a default.
_PARAM_INFO_REQUIRED = {'pi_disp_order', 'pi_display', 'pi_display_results'}

#: Exactly the keys of a link.
_LINK_KEYS = {
    'pi_category_name',
    'pi_disp_order',
    'pi_display',
    'pi_display_results',
    'pi_referred_slug',
}

#: Exactly the keys of a definition with no column.
_DEFINITION_KEYS = {'definition', 'pi_dict_context', 'pi_dict_name'}

#: The table-level entries, each a single key.
_TABLE_LEVEL_KEYS = {'constraint', 'foreign_key', *TABLE_LEVEL_KEY_KINDS}

#: The members a table-level ``foreign_key`` entry may have.
_FOREIGN_KEY_MEMBERS = {'columns', 'references', 'on_delete'}

#: The members it must have.
_FOREIGN_KEY_REQUIRED = {'columns', 'references'}

#: The ``field_key`` values `create_table` renders, besides False for none.
_FIELD_KEYS = {True, 'primary', 'unique', 'foreign'}

#: The schemas the dictionary step reads definitions from (`do_dictionary`).
_DEFINITION_SOURCES = ('obs*.json', 'internal_def*.json', 'mult_tooltips*.json')

#: The two places a column names a definition: the search form's, and the results'.
_DICTIONARY_SUFFIXES = ('', '_results')


class DuplicateKeyError(ValueError):
    """A JSON object names the same key twice."""


def _refuse_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object, refusing one that names a key twice.

    `json.loads` otherwise keeps the last value and drops the others without a word, so
    a key written twice in one entry is a value nobody can see is ignored.

    Parameters:
        pairs: The object's members, in the order written.

    Returns:
        The object.

    Raises:
        DuplicateKeyError: If a key appears more than once.
    """
    counts = Counter(key for key, _ in pairs)
    repeated = sorted(key for key, count in counts.items() if count > 1)
    if repeated:
        raise DuplicateKeyError(f'repeated key(s) {repeated}')
    return dict(pairs)


def _load(path: Path) -> Any:
    """Read a schema file, refusing any object that repeats a key.

    Parameters:
        path: The file.

    Returns:
        Its contents.
    """
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_refuse_duplicate_keys)


def _schema_files() -> list[Path]:
    """Return every packaged JSON file, sorted."""
    return sorted(_SCHEMA_DIR.glob('*.json'))


def _entry_lists() -> list[tuple[str, list[dict[str, Any]]]]:
    """Return every schema that is a list of entries, by file name."""
    return [
        (path.name, _load(path)) for path in _schema_files() if path.name not in _NOT_ENTRY_LISTS
    ]


def _columns() -> list[tuple[str, dict[str, Any]]]:
    """Return every column entry, with the file it is in."""
    return [
        (name, entry)
        for name, entries in _entry_lists()
        for entry in entries
        if 'field_name' in entry
    ]


def _where(name: str, entry: dict[str, Any]) -> str:
    """Name an entry for a failure message."""
    label = entry.get('field_name') or entry.get('pi_referred_slug') or entry.get('pi_dict_name')
    return f'{name}: {label}'


# ---------------------------------------------------------------------------
# The documents
# ---------------------------------------------------------------------------


def test_the_duplicate_key_check_catches_a_repeated_key() -> None:
    """The loader the checks below use refuses what `json.loads` would quietly accept."""
    text = '[{"field_name": "a", "field_type": "int4", "field_type": "text"}]'
    assert json.loads(text) == [{'field_name': 'a', 'field_type': 'text'}]
    with pytest.raises(DuplicateKeyError, match="'field_type'"):
        json.loads(text, object_pairs_hook=_refuse_duplicate_keys)


@pytest.mark.parametrize('path', _schema_files(), ids=lambda path: path.name)
def test_no_object_repeats_a_key(path: Path) -> None:
    """No entry names the same key twice, in any packaged JSON file."""
    _load(path)


@pytest.mark.parametrize('path', _schema_files(), ids=lambda path: path.name)
def test_every_schema_is_a_list_of_objects(path: Path) -> None:
    """A table schema is a non-empty list of entries, each an object."""
    if path.name in _NOT_ENTRY_LISTS:
        return
    entries = _load(path)
    assert isinstance(entries, list), path.name
    assert entries, path.name
    assert all(isinstance(entry, dict) for entry in entries), path.name


def test_every_entry_is_one_of_the_four_kinds() -> None:
    """Each entry's keys are exactly those of a column, a link, a definition or a table-level entry."""
    wrong: list[str] = []
    for name, entries in _entry_lists():
        for entry in entries:
            keys = set(entry)
            if 'field_name' in entry:
                if not keys <= _COLUMN_KEYS:
                    wrong.append(f'{_where(name, entry)}: unknown {sorted(keys - _COLUMN_KEYS)}')
                if not keys >= _COLUMN_REQUIRED:
                    wrong.append(
                        f'{_where(name, entry)}: missing {sorted(_COLUMN_REQUIRED - keys)}'
                    )
            elif 'pi_referred_slug' in entry:
                if keys != _LINK_KEYS:
                    wrong.append(f'{_where(name, entry)}: a link with {sorted(keys)}')
            elif 'definition' in entry:
                if keys != _DEFINITION_KEYS:
                    wrong.append(f'{_where(name, entry)}: a definition with {sorted(keys)}')
            elif len(keys) != 1 or not keys <= _TABLE_LEVEL_KEYS:
                wrong.append(f'{name}: an entry of no known kind, {sorted(keys)}')
            elif 'constraint' in entry:
                if not isinstance(entry['constraint'], str):
                    wrong.append(f'{name}: a constraint that is not text')
            elif 'foreign_key' in entry:
                wrong += _foreign_key_problems(name, entry['foreign_key'])
            else:
                (level_entry,) = keys
                wrong += _table_level_key_problems(name, entry, level_entry)
    assert wrong == []


def _table_level_key_problems(name: str, entry: dict[str, Any], level_entry: str) -> list[str]:
    """Say what is wrong with a table-level ``primary_key``, ``unique`` or ``key`` entry.

    Parameters:
        name: The file the entry is in.
        entry: The entry.
        level_entry: Which of the three it is.

    Returns:
        One line, or none for an entry `create_table` renders as written.
    """
    columns = entry[level_entry]
    if isinstance(columns, list) and columns and all(isinstance(c, str) for c in columns):
        return []
    return [f'{name}: {level_entry} {columns!r} is not a list of column names']


@pytest.mark.parametrize(
    ('entry', 'problem'),
    [
        ({'unique': ['a', 'b']}, False),
        ({'key': ['a', 'b', 'c']}, False),
        ({'primary_key': []}, True),
        ({'unique': 'a'}, True),
        ({'key': [1]}, True),
    ],
)
def test_the_table_level_key_check_refuses_what_create_table_cannot_render(
    entry: dict[str, Any], problem: bool
) -> None:
    """A key lists at least one column, by name."""
    (level_entry,) = entry
    assert bool(_table_level_key_problems('x.json', entry, level_entry)) == problem


def _foreign_key_problems(name: str, entry: Any) -> list[str]:
    """Say what is wrong with a table-level ``foreign_key`` entry, if anything.

    Parameters:
        name: The file the entry is in.
        entry: The entry's ``foreign_key`` value.

    Returns:
        One line per problem; none for an entry `create_table` renders as written.
    """
    if not isinstance(entry, dict):
        return [f'{name}: a foreign_key that is not an object']
    members = set(entry)
    problems = []
    if not members <= _FOREIGN_KEY_MEMBERS:
        problems.append(f'{name}: foreign_key with {sorted(members - _FOREIGN_KEY_MEMBERS)}')
    if not members >= _FOREIGN_KEY_REQUIRED:
        problems.append(f'{name}: foreign_key without {sorted(_FOREIGN_KEY_REQUIRED - members)}')
        return problems
    columns, references = entry['columns'], entry['references']
    if not isinstance(columns, list) or not columns or not all(isinstance(c, str) for c in columns):
        problems.append(f'{name}: foreign_key columns {columns!r} is not a list of names')
    elif (
        not isinstance(references, list)
        or len(references) != len(columns) + 1
        or not all(isinstance(r, str) for r in references)
    ):
        problems.append(
            f'{name}: foreign_key references {references!r} is not a table and a column '
            'for each column'
        )
    if 'on_delete' in entry and entry['on_delete'] not in ON_DELETE_VALUES:
        problems.append(f'{name}: foreign_key on_delete {entry["on_delete"]!r}')
    return problems


@pytest.mark.parametrize(
    ('entry', 'problem'),
    [
        ({'columns': ['a'], 'references': ['t', 'id']}, None),
        ({'columns': ['a'], 'references': ['t', 'id'], 'on_delete': 'cascade'}, None),
        ({'columns': ['a'], 'references': ['t', 'id'], 'on_delete': 'set null'}, 'on_delete'),
        ({'columns': ['a'], 'references': ['t']}, 'references'),
        ({'columns': [], 'references': ['t']}, 'columns'),
        ({'columns': ['a']}, 'without'),
        ({'columns': ['a'], 'references': ['t', 'id'], 'on_update': 'cascade'}, 'on_update'),
    ],
)
def test_the_foreign_key_check_refuses_what_create_table_cannot_render(
    entry: dict[str, Any], problem: str | None
) -> None:
    """A well-formed entry passes, and each kind of malformed one is named."""
    problems = _foreign_key_problems('x.json', entry)
    if problem is None:
        assert problems == []
    else:
        assert len(problems) == 1
        assert problem in problems[0]


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------


def test_every_field_type_is_one_create_table_renders() -> None:
    """The renderer and this check read the same constants (`importdb.mysql`)."""
    assert [
        f'{_where(name, column)}: {column["field_type"]!r}'
        for name, column in _columns()
        if not isinstance(column['field_type'], str)
        or not is_renderable_field_type(column['field_type'])
    ] == []


def test_the_renderable_types_include_every_type_the_schemas_use() -> None:
    """Defends the constant itself: a fixed type no schema uses is still a legal one."""
    used = {column['field_type'] for _, column in _columns()}
    assert MYSQL_ENUM_FIELD_TYPE in used
    assert used & set(MYSQL_FIELD_TYPE_SQL)


def test_every_enum_lists_its_values_and_nothing_else_does() -> None:
    """``field_enum_options`` belongs to an ``enum`` column, which needs it."""
    assert [
        _where(name, column)
        for name, column in _columns()
        if (column['field_type'] == MYSQL_ENUM_FIELD_TYPE)
        != isinstance(column.get('field_enum_options'), str)
    ] == []


def test_every_character_set_is_one_create_table_renders_on_a_text_column() -> None:
    """``field_charset`` names a set `create_table` knows, on a column holding text."""
    assert [
        f'{_where(name, column)}: {column["field_type"]} {column["field_charset"]!r}'
        for name, column in _columns()
        if 'field_charset' in column
        and (
            column['field_charset'] not in MYSQL_CHARSET_SQL
            or not takes_charset(column['field_type'])
        )
    ] == []


#: The columns that identify an observation, a bundle or a session wherever they appear,
#: which hold ASCII, a byte a character, so that every join, lookup and sort on them
#: reads fewer bytes; ``ascii_general_ci`` still compares them without case.
_ASCII_IDENTIFIERS = {'opus_id', 'bundle_id', 'session_id'}


def test_every_identifier_column_is_ascii() -> None:
    """An OPUS ID, a bundle ID or a session key is ASCII in every table that holds one."""
    columns = [
        (name, column) for name, column in _columns() if column['field_name'] in _ASCII_IDENTIFIERS
    ]
    assert {column['field_name'] for _, column in columns} == _ASCII_IDENTIFIERS
    assert [
        _where(name, column) for name, column in columns if column.get('field_charset') != 'ascii'
    ] == []


def test_every_key_is_one_create_table_renders() -> None:
    """A foreign key names its table and column, and only a foreign key does."""
    wrong: list[str] = []
    for name, column in _columns():
        key = column.get('field_key', False)
        foreign = column.get('field_key_foreign')
        if key is not False and key not in _FIELD_KEYS:
            wrong.append(f'{_where(name, column)}: field_key {key!r}')
        if (key == 'foreign') != (foreign is not None):
            wrong.append(f'{_where(name, column)}: field_key {key!r} with {foreign!r}')
        if foreign is not None and not (
            isinstance(foreign, list)
            and len(foreign) == 2
            and all(isinstance(x, str) for x in foreign)
        ):
            wrong.append(f'{_where(name, column)}: field_key_foreign {foreign!r}')
    assert wrong == []


@pytest.mark.parametrize(
    'flag', ['field_notnull', 'field_autoincrement', 'val_set_invalid_to_null']
)
def test_every_flag_is_a_boolean(flag: str) -> None:
    """A flag written as text or a number would read as true whatever it said."""
    assert [
        f'{_where(name, column)}: {column[flag]!r}'
        for name, column in _columns()
        if flag in column and not isinstance(column[flag], bool)
    ] == []


def test_every_column_with_a_param_info_row_has_what_the_step_reads() -> None:
    """The ``param_info`` step reads these without a default, so a missing one is a crash."""
    assert [
        f'{_where(name, column)}: missing {sorted(_PARAM_INFO_REQUIRED - set(column))}'
        for name, column in _columns()
        if 'pi_category_name' in column and not set(column) >= _PARAM_INFO_REQUIRED
    ] == []


def test_every_form_type_names_a_known_unit() -> None:
    """The ``param_info`` step refuses a unit `opus_support` does not know."""
    wrong: list[str] = []
    for name, column in _columns():
        form_type = column.get('pi_form_type')
        if form_type is None:
            continue
        _form, _format, unit_id = opus_support.parse_form_type(form_type)
        if unit_id and not opus_support.is_valid_unit_id(unit_id):
            wrong.append(f'{_where(name, column)}: {form_type!r}')
    assert wrong == []


def test_every_ranges_name_is_in_the_ranges_file() -> None:
    """The ``param_info`` step refuses a ``pi_ranges`` that ``param_info_ranges.json`` lacks."""
    ranges = _load(_SCHEMA_DIR / 'param_info_ranges.json')
    assert [
        f'{_where(name, column)}: {column["pi_ranges"]!r}'
        for name, column in _columns()
        if 'pi_ranges' in column and column['pi_ranges'] not in ranges
    ] == []


def test_every_mult_options_row_is_a_mult_row() -> None:
    """Seven values, typed as `import_util.MultOption` says, with integer orders.

    The pin and the group pin are integers, never strings of digits: the import refuses
    a string. An id fits ``mult.id``, a ``SMALLINT UNSIGNED``, below its largest value,
    which a pinned field's absent value takes when its list has none.
    """
    wrong: list[str] = []
    for name, column in _columns():
        rows = column.get('mult_options')
        if rows is None:
            continue
        for row in rows:
            if not isinstance(row, list) or len(row) != len(import_util.MultOption._fields):
                wrong.append(f'{_where(name, column)}: {row!r}')
                continue
            option = import_util.MultOption(*row)
            if not (
                _is_int(option.id)
                and 0 <= option.id < PINNED_ABSENT_ID
                and isinstance(option.value, str | None)
                and isinstance(option.label, str)
                and _is_int(option.pin)
                and option.display in ('Y', 'N')
                and isinstance(option.grouping, str | None)
                and (option.group_pin is None or _is_int(option.group_pin))
            ):
                wrong.append(f'{_where(name, column)}: {row!r}')
        ids = [row[0] for row in rows if isinstance(row, list) and row]
        if len(ids) != len(set(ids)):
            wrong.append(f'{_where(name, column)}: repeated ids')
    assert wrong == []


def _is_int(value: object) -> bool:
    """Return whether a JSON value is an integer, which a boolean is not."""
    return isinstance(value, int) and not isinstance(value, bool)


#: The members a ``mult_overrides`` entry may carry, each a column of ``mult``.
_OVERRIDE_MEMBERS = {'value', 'label', 'display', 'grouping', 'pin'}


def test_every_mult_overrides_entry_names_a_value_and_mult_columns() -> None:
    """An override is an object with a ``value`` and only `mult`'s presentation columns.

    It belongs to a column that holds mult ids and lists no ``mult_options``: a pinned
    field's presentation is its list.
    """
    wrong: list[str] = []
    for name, column in _columns():
        overrides = column.get('mult_overrides')
        if overrides is None:
            continue
        if not mult_fields.is_mult_column(column) or 'mult_options' in column:
            wrong.append(f'{_where(name, column)}: overrides on a column that cannot take them')
        for override in overrides:
            if not (
                isinstance(override, dict)
                and 'value' in override
                and set(override) <= _OVERRIDE_MEMBERS
                and isinstance(override.get('label', ''), str)
                and override.get('display', 'Y') in ('Y', 'N')
                and (override.get('pin') is None or _is_int(override['pin']))
            ):
                wrong.append(f'{_where(name, column)}: {override!r}')
    assert wrong == []


def test_every_mult_field_key_is_on_a_mult_column() -> None:
    """A ``mult_field`` key names the field of a column that holds mult ids."""
    wrong = [
        _where(name, column)
        for name, column in _columns()
        if 'mult_field' in column
        and not (isinstance(column['mult_field'], str) and mult_fields.is_mult_column(column))
    ]
    assert wrong == []


# ---------------------------------------------------------------------------
# The dictionary
# ---------------------------------------------------------------------------


def _definitions() -> list[tuple[str, str, str]]:
    """Return every ``(term, context, file)`` the dictionary step would create."""
    found: list[tuple[str, str, str]] = []
    for pattern in _DEFINITION_SOURCES:
        for path in sorted(_SCHEMA_DIR.glob(pattern)):
            for entry in _load(path):
                for suffix in _DICTIONARY_SUFFIXES:
                    if 'definition' + suffix in entry:
                        found.append(
                            (
                                entry.get('pi_dict_name' + suffix),
                                entry.get('pi_dict_context' + suffix),
                                path.name,
                            )
                        )
    return found


def test_every_definition_has_a_term_and_a_context() -> None:
    """The dictionary step refuses a definition missing either."""
    assert [
        f'{file}: {term!r} in {context!r}'
        for term, context, file in _definitions()
        if not isinstance(term, str) or not isinstance(context, str)
    ] == []


def test_no_two_definitions_share_a_term_and_a_context() -> None:
    """``definitions`` is unique on the pair, so a second one would fail the import."""
    counts = Counter((term, context) for term, context, _ in _definitions())
    assert sorted(pair for pair, count in counts.items() if count > 1) == []


def test_every_definition_is_filed_under_a_context_that_exists() -> None:
    """``definitions.context`` is a foreign key onto ``contexts.name``."""
    with (import_util.DICTIONARY_DATA_DIR / 'contexts.csv').open(encoding='utf-8') as csvfile:
        contexts = {row[0] for row in csv.reader(csvfile)}
    tooltip_files = sorted(_SCHEMA_DIR.glob('mult_tooltips*.json'))
    contexts |= {f'MULT_{path.stem[path.stem.rindex("_") + 1 :].upper()}' for path in tooltip_files}
    assert (
        sorted({(context, file) for _, context, file in _definitions() if context not in contexts})
        == []
    )


def test_every_tooltip_a_column_names_has_a_definition() -> None:
    """Each ``pi_dict_name`` and ``pi_dict_context`` pair, either kind, resolves.

    The web application looks a tooltip up by the pair ``param_info`` carries, and a pair
    with no definition is a tooltip that silently shows nothing.
    """
    defined = {(term, context) for term, context, _ in _definitions()}
    wrong: list[str] = []
    for name, column in _columns():
        for suffix in _DICTIONARY_SUFFIXES:
            term = column.get('pi_dict_name' + suffix)
            context = column.get('pi_dict_context' + suffix)
            if term is None and context is None:
                continue
            if (term, context) not in defined:
                wrong.append(f'{_where(name, column)}: {term!r} in {context!r}')
    assert wrong == []


# ---------------------------------------------------------------------------
# The junction tables of the list columns
# ---------------------------------------------------------------------------


def _list_columns() -> list[tuple[str, str]]:
    """Return every ``mult_list`` column, as its table and its name."""
    return [
        (name.removesuffix('.json'), entry['field_name'])
        for name, entry in _columns()
        if entry['field_type'] == list_junctions.LIST_FIELD_TYPE
    ]


def _junction_schema() -> list[dict[str, Any]]:
    """Return what a list column's junction schema must hold: the id and the observation,
    keyed ``(mult_id, obs_general_id)``, with the key the per-bundle delete reads and the
    foreign key onto ``obs_general``."""
    mult_id = list_junctions.JUNCTION_MULT_COLUMN
    observation = list_junctions.JUNCTION_OBSERVATION_COLUMN
    return [
        {'field_name': mult_id, 'field_type': 'mult_idx', 'field_notnull': True},
        {'field_name': observation, 'field_type': 'uint4', 'field_notnull': True},
        {'primary_key': [mult_id, observation]},
        {'key': [observation]},
        {'foreign_key': {'columns': [observation], 'references': ['obs_general', 'id']}},
    ]


def test_the_list_columns_are_on_obs_general() -> None:
    """A list column's junction table names its observation by ``obs_general_id``, and the
    application correlates it with ``obs_general``."""
    assert _list_columns()
    assert {table for table, _ in _list_columns()} == {'obs_general'}


def test_every_list_column_has_its_junction_schema() -> None:
    """Each ``mult_list`` column has a schema file named for its junction table, holding
    exactly the junction's columns and keys (the notes aside)."""
    wrong = []
    for table, column in _list_columns():
        junction = list_junctions.junction_table(table, column)
        path = _SCHEMA_DIR / f'{junction}.json'
        if not path.is_file():
            wrong.append(f'{junction}: no schema file')
            continue
        entries = [
            {key: value for key, value in entry.items() if key not in ('comment', 'comments')}
            for entry in _load(path)
        ]
        if entries != _junction_schema():
            wrong.append(f'{junction}: {entries}')
    assert wrong == []


def test_every_junction_schema_belongs_to_a_list_column() -> None:
    """A schema holding a ``mult_id`` column is a list column's junction table."""
    junctions = {list_junctions.junction_table(table, column) for table, column in _list_columns()}
    holding = {
        name.removesuffix('.json')
        for name, entry in _columns()
        if entry['field_name'] == list_junctions.JUNCTION_MULT_COLUMN
    }
    assert holding == junctions
