"""Build the ``table_names`` table, which orders the Details tab's sections.

One row per permanent ``obs_`` table that exists, plus ``obs_general``, which is written
unconditionally because every observation has one: the table's name, the heading the web
application shows above it, and whether it is shown at all. The rows are written in the
order they should appear, and ``disp_order`` counts up as they are appended, so the
order of the code below is the order a user sees.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opus_import import config_data, import_util

if TYPE_CHECKING:
    from opus_import.context import ImportContext


def create_import_table_names_table(ctx: ImportContext) -> None:
    """Fill the import ``table_names`` table from the permanent tables that exist.

    ``obs_general`` comes first and is written whether or not the table is there; then
    the PDS, image, wavelength, profile, surface geometry name and surface geometry
    tables, each only if it exists; then one row per surface geometry target in
    alphabetical order; then ring geometry; then the mission tables and the instrument
    tables. The HST instrument tables are written with ``display`` set to ``'N'``: HST
    puts its columns in the mission table, so its instrument tables would be empty
    sections.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', 'Creating new import table_names table')
    table_names_schema = import_util.read_schema_for_table(ctx, 'table_names')
    # table_names.json is packaged with opus_import, so the schema is always found.
    assert table_names_schema is not None
    # Start from scratch
    db.drop_table('import', 'table_names')
    db.create_table('import', 'table_names', table_names_schema,
                    ignore_if_exists=False)

    # We use the entries in data_config to determine what
    # goes into table_names. The order we do things here matters because we're
    # creating disp_order as we go. This will determine the order of how things
    # are displayed on the Details tab.

    rows: list[dict[str, Any]] = []
    disp_order = 0

    # obs_general first
    entry = {
        'table_name': 'obs_general',
        'label':      'General Constraints',
        'display':    'Y',
        'disp_order': disp_order
    }
    disp_order += 1
    rows.append(entry)

    # Then various random tables
    if db.table_exists('perm', 'obs_pds'):
        entry = {
            'table_name': 'obs_pds',
            'label':      'PDS Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if db.table_exists('perm', 'obs_type_image'):
        entry = {
            'table_name': 'obs_type_image',
            'label':      'Image Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if db.table_exists('perm', 'obs_wavelength'):
        entry = {
            'table_name': 'obs_wavelength',
            'label':      'Wavelength Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if db.table_exists('perm', 'obs_profile'):
        entry = {
            'table_name': 'obs_profile',
            'label':      'Occultation/Reflectance Profiles Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if db.table_exists('perm', 'obs_surface_geometry_name'):
        entry = {
            'table_name': 'obs_surface_geometry_name',
            'label':      'Surface Geometry Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if db.table_exists('perm', 'obs_surface_geometry'):
        entry = {
            'table_name': 'obs_surface_geometry',
            'label':      'Surface Geometry Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    surface_geo_table_names = db.table_names(
                                    'perm',
                                    prefix='obs_surface_geometry__')
    for table_name in sorted(surface_geo_table_names):
        target_name = table_name.replace('obs_surface_geometry__', '')
        target_name = import_util.decode_target_name(target_name).title()
        entry = {
            'table_name': table_name,
            'label':      target_name + ' Surface Geometry Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    if db.table_exists('perm', 'obs_ring_geometry'):
        entry = {
            'table_name': 'obs_ring_geometry',
            'label':      'Ring Geometry Constraints',
            'display':    'Y',
            'disp_order': disp_order
        }
        disp_order += 1
        rows.append(entry)

    # Then missions
    for mission_id in sorted(
        config_data.MISSION_ID_TO_MISSION_TABLE_SFX.keys()):
        table_name = 'obs_mission_'+config_data.MISSION_ID_TO_MISSION_TABLE_SFX[
                                                            mission_id]
        if db.table_exists('perm', table_name):
            entry = {
                'table_name': table_name,
                'label':      (config_data.MISSION_ID_TO_MISSION_NAME[mission_id] +
                               ' Mission Constraints'),
                'display':    'Y',
                'disp_order': disp_order
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
        table_name = 'obs_instrument_'+instrument_id.lower()
        if db.table_exists('perm', table_name):
            entry = {
                'table_name': table_name,
                'label':      (config_data.INSTRUMENT_ID_TO_INSTRUMENT_NAME[
                                                                        instrument_id]+
                               ' Constraints'),
                'display':    display,
                'disp_order': disp_order
            }
            disp_order += 1
            rows.append(entry)

    db.insert_rows('import', 'table_names', rows)

def copy_table_names_from_import_to_permanent(ctx: ImportContext) -> None:
    """Replace the permanent ``table_names`` table with the import one.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    db = ctx.db
    assert db is not None
    logger = ctx.logger

    logger.log('info', 'Copying table_names table from import to permanent')
    # Start from scratch
    table_names_schema = import_util.read_schema_for_table(ctx, 'table_names')
    # table_names.json is packaged with opus_import, so the schema is always found.
    assert table_names_schema is not None
    db.drop_table('perm', 'table_names')
    db.create_table('perm', 'table_names', table_names_schema,
                    ignore_if_exists=False)

    db.copy_rows_between_namespaces('import', 'perm', 'table_names')


def do_table_names(ctx: ImportContext) -> None:
    """Rebuild the permanent ``table_names`` table, driven by ``--create-table-names``.

    Parameters:
        ctx: The import run's context, for the open database and the logger.
    """
    create_import_table_names_table(ctx)
    copy_table_names_from_import_to_permanent(ctx)
    assert ctx.db is not None
    ctx.db.drop_table('import', 'table_names')
