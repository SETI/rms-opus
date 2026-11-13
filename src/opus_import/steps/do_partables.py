"""Build the ``partables`` table, which says what a search reveals.

A row maps a value a user can search for onto a table of further search parameters that
value makes relevant: choosing the Cassini mission, for instance, reveals the Cassini
mission table. The web application reads this to decide which sections of the search
form to offer, so a mission or instrument with no row here has no searchable columns of
its own.

Every trigger names the id of a ``mult`` row, because that is what the column it
triggers on holds: an ``obs_general`` column for a mission, an instrument or an
instrument host, and the surface geometry selector for a body.

The table is built beside the live one and swapped in (`opus_import.table_swap`), so the
step can run on a schema that is being served.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opus_import import config_data, import_util, surface_geometry, table_swap
from opus_import.steps.do_import_mult import mult_table_lookup_id

if TYPE_CHECKING:
    from collections.abc import Sequence

    from opus_import.context import ImportContext


def _lookup_table_column(
    table_schema: Sequence[dict[str, Any]], column_name: str
) -> dict[str, Any] | None:
    """Return one column's definition out of a table schema.

    Parameters:
        table_schema: The table's column definitions.
        column_name: The column to find.

    Returns:
        The column's definition, or None if the schema has no such column.
    """
    for table_column in table_schema:
        if table_column.get('field_name', None) == column_name:
            return table_column
    return None


def fill_partables(ctx: ImportContext, new_table: str) -> bool:
    """Fill an empty ``partables`` table with every trigger OPUS knows.

    One row per mission, per instrument and per instrument host, each keyed by the
    mult id of the corresponding ``obs_general`` value, plus one per surface
    geometry body ``obs_surface_geometry_target`` holds
    (`opus_import.surface_geometry.stored_targets`), keyed by the body's id in the
    selector's mult field and revealing the body's category. An HST instrument points at the Hubble
    mission table, because HST keeps its columns there rather than in an instrument
    table of its own.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        new_table: The table to fill, already created from ``partables``'s
            schema.

    Returns:
        True; every row is built from what the imported tables hold.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', f'Filling {new_table}')

    # We use the entries in data_config to determine the first part of what
    # goes into partables.

    # For obs_general, we care about mission_id, inst_host_id, instrument_id,
    # and type_id.

    obs_general_schema = import_util.read_schema_for_table(ctx, 'obs_general')
    # obs_general.json is packaged with opus_import, so the schema is always found.
    assert obs_general_schema is not None

    rows: list[dict[str, Any]] = []

    mission_id_column = _lookup_table_column(obs_general_schema, 'mission_id')
    assert mission_id_column is not None
    for mission_id in sorted(config_data.MISSION_ID_TO_MISSION_TABLE_SFX.keys()):
        mission_id_val = mult_table_lookup_id(
            ctx, 'obs_general', 'mission_id', mission_id_column, mission_id
        )
        entry = {
            'trigger_tab': 'obs_general',
            'trigger_col': 'mission_id',
            'trigger_val': str(mission_id_val),
            'partable': import_util.table_name_obs_mission(mission_id),
        }
        rows.append(entry)

    instrument_id_column = _lookup_table_column(obs_general_schema, 'instrument_id')
    assert instrument_id_column is not None
    for instrument_id in sorted(config_data.INSTRUMENT_ID_TO_MISSION_ID.keys()):
        instrument_id_val = mult_table_lookup_id(
            ctx, 'obs_general', 'instrument_id', instrument_id_column, instrument_id
        )
        partable = import_util.table_name_obs_instrument(instrument_id)
        if instrument_id[:3] == 'HST':
            # This is a hack because we don't actually have HST instrument
            # tables, but instead put everything in the mission tables
            partable = 'obs_mission_hubble'
        entry = {
            'trigger_tab': 'obs_general',
            'trigger_col': 'instrument_id',
            'trigger_val': str(instrument_id_val),
            'partable': partable,
        }
        rows.append(entry)

    inst_host_id_column = _lookup_table_column(obs_general_schema, 'inst_host_id')
    assert inst_host_id_column is not None
    for inst_host_id in sorted(config_data.INST_HOST_ID_TO_MISSION_ID.keys()):
        inst_host_id_val = mult_table_lookup_id(
            ctx, 'obs_general', 'inst_host_id', inst_host_id_column, inst_host_id
        )
        entry = {
            'trigger_tab': 'obs_general',
            'trigger_col': 'inst_host_id',
            'trigger_val': str(inst_host_id_val),
            'partable': (
                'obs_mission_'
                + config_data.MISSION_ID_TO_MISSION_TABLE_SFX[
                    config_data.INST_HOST_ID_TO_MISSION_ID[inst_host_id]
                ]
            ),
        }
        rows.append(entry)

    # We don't need this anymore because Image Constraints are now permanently
    # displayed
    # entry = {
    #     'trigger_tab': 'obs_general',
    #     'trigger_col': 'data_type',
    #     'trigger_val': 'IMG',
    #     'partable':    'obs_type_image'
    # }
    # rows.append(entry)

    for target in surface_geometry.stored_targets(ctx):
        entry = {
            'trigger_tab': surface_geometry.SELECTOR_CATEGORY,
            'trigger_col': surface_geometry.TARGET_COLUMN,
            'trigger_val': str(target.target_id),
            'partable': surface_geometry.target_category(target.encoded_name),
        }
        rows.append(entry)

    db.insert_rows(new_table, rows)
    return True


def do_partables(ctx: ImportContext) -> None:
    """Rebuild the ``partables`` table, driven by ``--create-partables``.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    new_name = table_swap.swap_new_name('partables')
    table_swap.rebuild_tables_by_swap(ctx, ['partables'], lambda: fill_partables(ctx, new_name))
