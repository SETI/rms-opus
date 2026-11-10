"""Build the ``table_names`` table, which orders the Details tab's sections.

A row carries a table's name, the heading the web application shows above it, and
whether it is shown at all. The rows are written in the order they should appear, and
``disp_order`` counts up as they are appended, so the order of the code below is the
order a user sees.

**The set of tables is written out by hand here, not derived from the schemas**, so a
table added to `opus_import.config_data` needs a row adding here too or it will have no
section. ``obs_files`` is deliberately absent: it holds one row per file rather than per
observation and users never search it.

The table is built beside the live one and swapped in (`opus_import.table_swap`), so the
step can run on a schema that is being served.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opus_import import config_data, import_util, table_swap

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from opus_import.context import ImportContext


def build_table_names_rows(
    table_exists: Callable[[str], bool], surface_geometry_table_names: Iterable[str]
) -> list[dict[str, Any]]:
    """Return the ``table_names`` rows for a set of tables, in display order.

    ``obs_general`` comes first and is written whether or not the table is there; then
    the PDS, image, wavelength, profile, surface geometry name and surface geometry
    tables, each only if it exists; then one row per surface geometry target in
    alphabetical order; then ring geometry; then the mission tables and the instrument
    tables. The HST instrument tables are written with ``display`` set to ``'N'``: HST
    puts its columns in the mission table, so its instrument tables would be empty
    sections.

    This is the authority on what a category is called and what order the categories
    come in. It is separated from the import step so that the documentation build can
    ask the same question about the packaged schemas without a database.

    Parameters:
        table_exists: Answers whether a table of the given name is there.
        surface_geometry_table_names: The per-target surface geometry tables, named in
            full (``obs_surface_geometry__<target>``). They are sorted here.

    Returns:
        One row per table, carrying ``table_name``, ``label``, ``display`` and a
        ``disp_order`` counting up from zero in the order returned.
    """
    # We use the entries in data_config to determine what
    # goes into table_names. The order we do things here matters because we're
    # creating disp_order as we go. This will determine the order of how things
    # are displayed on the Details tab.

    rows: list[dict[str, Any]] = []
    disp_order = 0

    # obs_general first
    entry = {
        'table_name': 'obs_general',
        'label': 'General Constraints',
        'display': 'Y',
        'disp_order': disp_order,
    }
    disp_order += 1
    rows.append(entry)

    # Then various random tables
    if table_exists('obs_pds'):
        entry = {
            'table_name': 'obs_pds',
            'label': 'PDS Constraints',
            'display': 'Y',
            'disp_order': disp_order,
        }
        disp_order += 1
        rows.append(entry)

    if table_exists('obs_type_image'):
        entry = {
            'table_name': 'obs_type_image',
            'label': 'Image Constraints',
            'display': 'Y',
            'disp_order': disp_order,
        }
        disp_order += 1
        rows.append(entry)

    if table_exists('obs_wavelength'):
        entry = {
            'table_name': 'obs_wavelength',
            'label': 'Wavelength Constraints',
            'display': 'Y',
            'disp_order': disp_order,
        }
        disp_order += 1
        rows.append(entry)

    if table_exists('obs_profile'):
        entry = {
            'table_name': 'obs_profile',
            'label': 'Occultation/Reflectance Profiles Constraints',
            'display': 'Y',
            'disp_order': disp_order,
        }
        disp_order += 1
        rows.append(entry)

    if table_exists('obs_surface_geometry_name'):
        entry = {
            'table_name': 'obs_surface_geometry_name',
            'label': 'Surface Geometry Constraints',
            'display': 'Y',
            'disp_order': disp_order,
        }
        disp_order += 1
        rows.append(entry)

    if table_exists('obs_surface_geometry'):
        entry = {
            'table_name': 'obs_surface_geometry',
            'label': 'Surface Geometry Constraints',
            'display': 'Y',
            'disp_order': disp_order,
        }
        disp_order += 1
        rows.append(entry)

    for table_name in sorted(surface_geometry_table_names):
        target_name = table_name.replace('obs_surface_geometry__', '')
        target_name = import_util.decode_target_name(target_name).title()
        entry = {
            'table_name': table_name,
            'label': target_name + ' Surface Geometry Constraints',
            'display': 'Y',
            'disp_order': disp_order,
        }
        disp_order += 1
        rows.append(entry)

    if table_exists('obs_ring_geometry'):
        entry = {
            'table_name': 'obs_ring_geometry',
            'label': 'Ring Geometry Constraints',
            'display': 'Y',
            'disp_order': disp_order,
        }
        disp_order += 1
        rows.append(entry)

    # Then missions
    for mission_id in sorted(config_data.MISSION_ID_TO_MISSION_TABLE_SFX.keys()):
        table_name = 'obs_mission_' + config_data.MISSION_ID_TO_MISSION_TABLE_SFX[mission_id]
        if table_exists(table_name):
            entry = {
                'table_name': table_name,
                'label': (
                    config_data.MISSION_ID_TO_MISSION_NAME[mission_id] + ' Mission Constraints'
                ),
                'display': 'Y',
                'disp_order': disp_order,
            }
            disp_order += 1
            rows.append(entry)

    # Then instruments
    for instrument_id in sorted(config_data.INSTRUMENT_ID_TO_MISSION_ID.keys()):
        display = 'Y'
        if instrument_id[:3] == 'HST':
            # This is a hack because we don't actually have HST instrument
            # tables, but instead put everything in the mission tables
            display = 'N'
        table_name = 'obs_instrument_' + instrument_id.lower()
        if table_exists(table_name):
            entry = {
                'table_name': table_name,
                'label': (
                    config_data.INSTRUMENT_ID_TO_INSTRUMENT_NAME[instrument_id] + ' Constraints'
                ),
                'display': display,
                'disp_order': disp_order,
            }
            disp_order += 1
            rows.append(entry)

    return rows


def fill_table_names(ctx: ImportContext, new_table: str) -> bool:
    """Fill an empty ``table_names`` table from the tables that exist.

    The rows and their order come from `build_table_names_rows`; this function only
    asks the database which tables are there and writes what it gets back.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
        new_table: The table to fill, already created from ``table_names``'s
            schema.

    Returns:
        True; every row is built from what the imported tables hold.
    """
    db = ctx.db
    assert db is not None
    ctx.logger.log('info', f'Filling {new_table}')

    rows = build_table_names_rows(
        lambda name: db.table_exists(name),
        db.table_names(prefix='obs_surface_geometry__'),
    )

    db.insert_rows(new_table, rows)
    return True


def do_table_names(ctx: ImportContext) -> None:
    """Rebuild the ``table_names`` table, driven by ``--create-table-names``.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    new_name = table_swap.swap_new_name('table_names')
    table_swap.rebuild_tables_by_swap(ctx, ['table_names'], lambda: fill_table_names(ctx, new_name))
