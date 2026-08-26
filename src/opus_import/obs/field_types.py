"""The types an obs class's ``field_obs_<table>_<column>`` method may return.

Each of those methods computes one column of one OPUS table, and the column's entry in
the packaged ``table_schemas`` JSON already says what it holds. These aliases are that
statement written in the type system, so the schema and the code can be cross-checked
rather than kept in step by hand: ``tests/opus_import/test_obs_field_annotations.py``
resolves every method against its schema column and fails if the two disagree.

Which alias a column takes is decided by the schema alone, in this order:

.. list-table::
   :header-rows: 1

   * - ``pi_form_type`` (up to any ``:``)
     - ``field_type``
     - alias
   * - ``GROUP``
     - any
     - `MultFieldRet`
   * - ``MULTIGROUP``
     - ``mult_list``
     - ``list[MultField]``
   * - anything else
     - ``char*``, ``varchar*``, ``text``, ``json``
     - `StrField`
   * - anything else
     - ``real4``, ``real8``
     - `FloatField`
   * - anything else
     - ``int*``, ``uint*``
     - `IntField`

**The form type is what decides, not the storage type**, and the difference is not a
formality. A ``flag_yesno`` or ``flag_onoff`` column is stored as ``int unsigned``
exactly like a ``mult_idx`` one (`opus_import.importdb.mysql.ImportDBMySQL.create_table`
maps all three the same way): it is an index into a ``mult_`` table, and its method
returns a `MultField` like any other group column. So does the one ``char3`` column that
carries a ``GROUP`` form type. Reading the storage type instead would annotate those
methods as scalars and be wrong about every one of them.

Returning a bare value from a group column is not merely untidy: it makes
`opus_import.steps.do_import_obs.import_observation_table` log
``bad data type returned for mult`` and discard the whole observation, because the
presentation lists it reads off the returned dictionary are never populated. That is why
the group aliases admit no bare values.

This module is named ``field_types`` rather than ``typing`` because ruff's ``A005``
forbids shadowing a standard-library module name.
"""

from __future__ import annotations

from typing import TypedDict

StrField = str | None
"""A text column's value, or None where the observation has none.

Covers ``char*``, ``varchar*`` and ``text`` columns, and the one ``json`` column
(``obs_general.preview_images``), whose method returns the output of `json.dumps` and so
is text as far as the pipeline is concerned. That one method never actually returns
None -- its column is ``field_notnull`` -- but it shares the alias rather than being
given one of its own for a single column.
"""

FloatField = float | None
"""A ``real4`` or ``real8`` column's value, or None where the observation has none."""

IntField = int | None
"""An ``int*`` or ``uint*`` column's value, or None where the observation has none."""


class MultField(TypedDict):
    """One value of a group column, together with how the web application shows it.

    `opus_import.obs.obs_base.ObsBase._create_mult` builds these and every group
    column's method returns one (or a list of them, for a ``MULTIGROUP`` column).
    `opus_import.steps.do_import_obs.import_observation_table` takes the eight keys
    apart into eight parallel lists and hands them to
    `opus_import.steps.do_import_mult.update_mult_table`, which turns ``col_val`` into
    the row id the ``obs_`` column actually stores.

    Two keys are carried but unused, and are kept because removing a key from a shape
    the whole hierarchy builds is a wider change than annotating it: **nothing anywhere
    reads** ``tooltip`` -- a ``mult_`` table has no such column -- and no obs class
    passes either ``tooltip`` or ``aliases``, so both are None in every row this
    pipeline writes today.

    Attributes:
        col_val: The value itself, before
            `opus_import.steps.do_import_obs.import_observation_table` normalizes a flag
            column's spelling and before `update_mult_table` renders it with ``str``.
            It is ``str | int | None`` rather than ``str | None`` because numeric
            enumerations reach it as numbers: ``obs_volume_vg2810`` passes the literal
            ``0`` for ``filter_number``, and the VGISS and GOSSI ``filter_number``
            methods pass a PDS index column that holds an integer.
        disp: ``'Y'`` to offer the value in the search form, ``'N'`` to hide it.
        disp_name: How the value is shown to users, or None to have
            `update_mult_table` derive a label from ``col_val``.
        disp_order: The sort key, or None to have `update_mult_table` derive one.
        grouping: The group the value belongs to in the search form, or None.
        group_disp_order: The group's sort key, or None to sort groups by name. It is
            text, not a number: both call sites pass a
            `opus_import.config_targets.PLANET_GROUP_MAPPING` entry's ``disp_order``,
            which is ``'010'``-style, and of the 410 ``mult_options`` entries in the
            packaged schemas the 54 that set the equivalent column set it to a string.
        tooltip: Unused. See above.
        aliases: Other spellings a search should accept, already rendered by
            `json.dumps` -- `_create_mult` converts the list it is handed. Unused; see
            above.
    """

    col_val: str | int | None
    disp: str
    disp_name: str | None
    disp_order: int | str | None
    grouping: str | None
    group_disp_order: str | None
    tooltip: str | None
    aliases: str | None


MultFieldRet = MultField | list[MultField]
"""What a ``GROUP`` column's method returns.

`opus_import.steps.do_import_obs.import_observation_table` wraps a single value in a
list before reading it, so a method may return either. A ``MULTIGROUP`` column is
annotated ``list[MultField]`` instead, because it is the only kind whose column really
does hold several values; a ``GROUP`` column that returned more than one would trip that
function's assertion that a non-``mult_list`` column produced exactly one value.
"""
