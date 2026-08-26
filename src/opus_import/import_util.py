"""General utilities the import pipeline's steps and obs classes share.

Five unrelated groups of helper live here:

* expanding the bundle descriptors given on the command line into bundle ids, and
  reading a PDS index table -- where a bad PDS3 label is reported and turned into a
  ``(None, None)`` result, while the PDS4 reader has no such handling and propagates;
* naming things -- the ``obs_``/``mult_`` table for a mission, instrument or surface
  geometry target, and the encoded and slug forms of a target name;
* reading the packaged ``table_schemas`` JSON that defines every OPUS table;
* logging, as thin ``log_*`` wrappers over `opus_import.context.ImportLog` so a step can
  log without reaching through the context, plus `NoDupLogger` for the PdsFile warnings
  an import run would otherwise produce hundreds of thousands of;
* a cached time conversion and a path join that is stable across operating systems.

Two of those hold state that outlives a call and is deliberately never cleared:
`NoDupLogger`'s record of what it has already logged, which is class-level and shared by
every instance, and `cached_tai_from_iso`'s cache. Nothing else in the module does.
"""

from __future__ import annotations

import csv
import fnmatch
import json
import os
import re
import sys
import traceback
from functools import lru_cache
from importlib.resources import files
from typing import TYPE_CHECKING, Any, ClassVar, Literal

import julian
import numpy as np
import pdsfile
import pdsparser
import pdstable

from opus_config import get_config
from opus_import import config_data, config_targets, instruments

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from importlib.abc import Traversable

    import pdslogger

    from opus_import.context import ImportContext
    from opus_import.importdb.super import Namespace

IndexRow = dict[str, Any]
"""One row of a PDS index table, keyed by column name."""

TableSchema = list[dict[str, Any]]
"""One OPUS table's definition: its columns, in order, as the JSON schema lists them.

An element is the same thing as an `opus_import.importdb.super.SchemaColumn`; the two
aliases are spelled separately so that neither package has to import the other.
"""

# Data that ships inside the package, located through importlib.resources rather than
# from __file__ or the working directory so that it is found in an installed wheel too:
# the JSON schemas that define every OPUS table, and the PDS data dictionary sources the
# dictionary import step reads.
TABLE_SCHEMA_DIR = files('opus_import') / 'table_schemas'
DICTIONARY_DATA_DIR = files('opus_import') / 'dictionary_data'

################################################################################
# GENERAL UTILITIES
################################################################################

# This is necessary because NHK2LO needs to come after NHKELO. See issue #1392.
# We go ahead and arrange the other volumes in chronological order as well.
# Also this allows us to only import the 1xxx volumes. The 2xxx volumes are
# calibrated data that show up as a download product and are not really separate
# volumes.
_NHXXLO_BUNDLES = [
    'NHLALO_1001',
    'NHJULO_1001',
    'NHPCLO_1001',
    'NHPELO_1001',
    'NHKCLO_1001',
    'NHKELO_1001',
    'NHK2LO_1001',
]

# Might as well do the same for NHxxMV.
_NHXXMV_BUNDLES = [
    'NHLAMV_1001',
    'NHJUMV_1001',
    'NHPCMV_1001',
    'NHPEMV_1001',
    'NHKCMV_1001',
    'NHKEMV_1001',
]

def yield_import_bundle_ids(ctx: ImportContext) -> Iterator[str]:
    """Yield the bundle ids named on the command line, in the order they import.

    The ``bundles`` arguments hold bundle descriptors, which are bundle ids, bundleset
    names, or the mission and instrument shorthands (``ALL``, ``CASSINI``, ``COISS``,
    ``VOYAGER``, ``HST``, and the rest) that stand for a fixed list of bundlesets. Each
    is validated as a PDS3 and then a PDS4 path, each bundleset is expanded into its
    bundles, and anything in ``--exclude-bundles`` is dropped.

    A New Horizons bundleset yields its calibrated (``2xxx``) bundle before its raw
    (``1xxx``) one, reversing the order the bundleset lists them in. The raw bundle is
    imported second so that it is the one holding the primary filespec, which is what
    ``pdsfile`` reports for those observations.

    Parameters:
        ctx: The import run's context, for the arguments and the logger.

    Yields:
        One bundle id per bundle to import.

    Raises:
        SystemExit: If any descriptor is not a bundle or bundleset that exists. Every
            bad descriptor is logged first, so one run reports all of them.
    """
    bundle_descs = []
    exclude_list = []
    if ctx.args.exclude_bundles:
        exclude_list = ctx.args.exclude_bundles.split(',')
    if ctx.args.bundles:
        for bundles in ctx.args.bundles:
            orig_bundle_descs = bundles.split(',')
            for desc in orig_bundle_descs:
                if desc.upper() == 'ALL':
                    bundle_descs.append('COISS_1xxx')
                    bundle_descs.append('COISS_2xxx')
                    bundle_descs.append('COCIRS_0xxx')
                    bundle_descs.append('COCIRS_1xxx')
                    bundle_descs.append('COCIRS_5xxx')
                    bundle_descs.append('COCIRS_6xxx')
                    bundle_descs.append('COUVIS_0xxx')
                    bundle_descs.append('COVIMS_0xxx')
                    bundle_descs.append('VGISS_5xxx')
                    bundle_descs.append('VGISS_6xxx')
                    bundle_descs.append('VGISS_7xxx')
                    bundle_descs.append('VGISS_8xxx')
                    bundle_descs.append('GO_0xxx')
                    bundle_descs.append('HSTIx_xxxx')
                    bundle_descs.append('HSTJx_xxxx')
                    bundle_descs.append('HSTNx_xxxx')
                    bundle_descs.append('HSTOx_xxxx')
                    bundle_descs.append('HSTUx_xxxx')
                    bundle_descs.extend(_NHXXLO_BUNDLES)
                    bundle_descs.extend(_NHXXMV_BUNDLES)
                    bundle_descs.append('EBROCC_xxxx')
                    bundle_descs.append('CORSS_8xxx')
                    bundle_descs.append('COUVIS_8xxx')
                    bundle_descs.append('COVIMS_8xxx')
                    bundle_descs.append('VG_28xx')
                    bundle_descs.append('uranus_occs_earthbased')
                    bundle_descs.append('cassini_uvis_solarocc_beckerjarmak2023')
                    bundle_descs.append('cassini_iss_fring_mosaics_rsfrench2025')
                elif desc.upper() == 'CASSINI':
                    bundle_descs.append('COISS_1xxx')
                    bundle_descs.append('COISS_2xxx')
                    bundle_descs.append('COCIRS_0xxx')
                    bundle_descs.append('COCIRS_1xxx')
                    bundle_descs.append('COCIRS_5xxx')
                    bundle_descs.append('COCIRS_6xxx')
                    bundle_descs.append('COUVIS_0xxx')
                    bundle_descs.append('COVIMS_0xxx')
                    bundle_descs.append('CORSS_8xxx')
                    bundle_descs.append('COUVIS_8xxx')
                    bundle_descs.append('COVIMS_8xxx')
                elif desc.upper() == 'COISS':
                    bundle_descs.append('COISS_1xxx')
                    bundle_descs.append('COISS_2xxx')
                elif desc.upper() == 'COCIRS':
                    bundle_descs.append('COCIRS_0xxx')
                    bundle_descs.append('COCIRS_1xxx')
                    bundle_descs.append('COCIRS_5xxx')
                    bundle_descs.append('COCIRS_6xxx')
                elif desc.upper() == 'COUVIS':
                    bundle_descs.append('COUVIS_0xxx')
                    bundle_descs.append('COUVIS_8xxx')
                elif desc.upper() == 'COVIMS':
                    bundle_descs.append('COVIMS_0xxx')
                    bundle_descs.append('COVIMS_8xxx')
                elif desc.upper() == 'CORSS':
                    bundle_descs.append('CORSS_8xxx')
                elif desc.upper() == 'VOYAGER':
                    bundle_descs.append('VGISS_5xxx')
                    bundle_descs.append('VGISS_6xxx')
                    bundle_descs.append('VGISS_7xxx')
                    bundle_descs.append('VGISS_8xxx')
                    bundle_descs.append('VG_28xx')
                elif desc.upper() == 'VGISS':
                    bundle_descs.append('VGISS_5xxx')
                    bundle_descs.append('VGISS_6xxx')
                    bundle_descs.append('VGISS_7xxx')
                    bundle_descs.append('VGISS_8xxx')
                    bundle_descs.append('VG_2810')
                elif desc.upper() == 'VGPPS':
                    bundle_descs.append('VG_2801')
                elif desc.upper() == 'VGUVS':
                    bundle_descs.append('VG_2802')
                elif desc.upper() == 'VGRSS':
                    bundle_descs.append('VG_2803')
                elif desc.upper() == 'GALILEO' or desc.upper() == 'GOSSI':
                    bundle_descs.append('GO_0xxx')
                elif desc.upper() == 'HST' or desc.upper() == 'HUBBLE':
                    bundle_descs.append('HSTIx_xxxx')
                    bundle_descs.append('HSTJx_xxxx')
                    bundle_descs.append('HSTNx_xxxx')
                    bundle_descs.append('HSTOx_xxxx')
                    bundle_descs.append('HSTUx_xxxx')
                elif desc.upper() == 'NH' or desc.upper() == 'NEWHORIZONS':
                    bundle_descs.extend(_NHXXLO_BUNDLES)
                    bundle_descs.extend(_NHXXMV_BUNDLES)
                elif desc.upper() == 'NHLORRI':
                    bundle_descs.extend(_NHXXLO_BUNDLES)
                elif desc.upper() == 'NHMVIC':
                    bundle_descs.extend(_NHXXMV_BUNDLES)
                elif desc.upper() == 'EBROCC':
                    bundle_descs.append('EBROCC_xxxx')
                else:
                    bundle_descs.append(desc)
        # First make sure everything is valid
        any_invalid = False
        for bundle_desc in bundle_descs:
            if bundle_desc in exclude_list:
                continue
            good_bundle = False
            # Try it as PDS3 and then PDS4
            try:
                bundle_pdsfile = pdsfile.pds3file.Pds3File.from_path(bundle_desc)
                good_bundle = True
            except (KeyError, ValueError):
                tb_pds3 = traceback.format_exc()
                try:
                    bundle_pdsfile = pdsfile.pds4file.Pds4File.from_path(bundle_desc)
                    good_bundle = True
                except (KeyError, ValueError):
                    any_invalid = True
                    msg = f'Bad bundle descriptor {bundle_desc}'
                    if not ctx.args.log_suppress_traceback:
                        msg += ':\n\n'
                        msg += ('*' * 80) + '\nPDS3:\n\n'
                        msg += tb_pds3
                        msg += '\n' + ('*' * 80) + '\nPDS4:\n\n'
                        msg += traceback.format_exc()
                    ctx.logger.log('fatal', msg)
            if good_bundle:
                if (not bundle_pdsfile.is_bundle_dir and
                    not bundle_pdsfile.is_bundleset_dir):
                    any_invalid = True
                    ctx.logger.log(
                        'fatal',
                        f'Bundle descriptor not a bundle or bundleset: {bundle_desc}')
                if not bundle_pdsfile.exists:
                    any_invalid = True
                    ctx.logger.log('fatal',
                                   f'Bundle descriptor not found: {bundle_desc}')

        if any_invalid:
            sys.exit(-1)

        # Expand the bundlesets
        new_bundledescs = []
        for bundle_desc in bundle_descs:
            try:
                bundle_pdsfile = pdsfile.pds3file.Pds3File.from_path(bundle_desc)
            except (KeyError, ValueError):
                bundle_pdsfile = pdsfile.pds4file.Pds4File.from_path(bundle_desc)
            if bundle_pdsfile.is_bundleset_dir:
                childnames = bundle_pdsfile.childnames
                # Make sure 2001 is imported first and then 1001 second for each
                # New Horizon bundle. That way, the primary filespec will be
                # raw in OPUS (same as pdsfile).
                if bundle_pdsfile.bundleset.startswith("NH"):
                    childnames.reverse()
                new_bundledescs += childnames
            else:
                new_bundledescs.append(bundle_desc)

        # Now actually return the bundle_ids
        for bundle_id in new_bundledescs:
            if bundle_id in exclude_list:
                ctx.logger.log('info', f'Excluding bundle: {bundle_id}')
                continue
            if bundle_id.find('.') != -1:
                continue # Sometimes a bad tar file gets stuck in the dir
            yield bundle_id

def log_accumulated_warnings(ctx: ImportContext, title: str) -> bool:
    """Report the Python warnings raised since the last report, and clear them.

    Parameters:
        ctx: The import run's context, which collects the warnings.
        title: What the warnings happened during, named in the heading.

    Returns:
        True if there were any warnings, which also marks the import as having produced
        bad data.
    """
    if len(ctx.python_warning_list) > 0:
        log_error(ctx, f'Warnings found during {title}:')
        for w in ctx.python_warning_list:
            log_error(ctx, '  '+w)
        ctx.python_warning_list = []
        ctx.import_has_bad_data = True
        return True
    return False

def safe_pdstable_read(ctx: ImportContext, filename: str,
                       pds_version: Literal[3, 4]
                       ) -> tuple[list[IndexRow] | None, dict[str, Any] | None]:
    """Read a PDS index table.

    Parameters:
        ctx: The import run's context, for the arguments and the logger.
        filename: The index file. For PDS3 this is the label; for PDS4 it is the CSV
            itself, because the PDS4 index files OPUS reads carry no label.
        pds_version: 3 or 4.

    Returns:
        The rows and the label. A PDS4 file has no label, so the second element is
        always None; its column values are strings unless every value in the column
        parses as an int, or as a float, in which case the whole column is converted.
        For PDS3 a file that could not be read gives ``(None, None)`` rather than
        raising, and the reason is logged.

    Raises:
        OSError: If a PDS4 CSV cannot be opened. Only the PDS3 path reports a bad file
            instead of raising.
    """
    if pds_version == 3:
        return safe_pdstable_read_pds3(ctx, filename)

    # TODOPDS4 For now, PDS4 index files do not have labels. They are just
    # CSV files. So we read the CSV file and determine the column names from
    # the single header line. We then infer the datatypes from the column data.
    # Eventually we will want to change this to use an official PDS4 label/table
    # reader module.

    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    if len(rows) == 0:
        # Both elements, like every other return here: the callers unpack a pair.
        return rows, None

    # Infer data types from the data in each column
    for col_name in rows[0]:
        col_data = [row[col_name] for row in rows]
        # First check if they are all integers
        try:
            _ = [int(x) for x in col_data]
        except ValueError: # Something parsed badly
            # Now check if they are all floats
            try:
                _ = [float(x) for x in col_data]
            except ValueError: # Something parsed badly
                # Not ints or floats, just leave them as strings and strip surrounding spaces
                # pass
                for row in rows:
                    row[col_name] = row[col_name].strip()
            else: # All floats
                for row in rows:
                    row[col_name] = float(row[col_name])

        else: # All integers
            for row in rows:
                row[col_name] = int(row[col_name])

    return rows, None  # TODOPDS4 There is no label for now

def safe_pdstable_read_pds3(ctx: ImportContext,
                            filename: str) -> tuple[list[IndexRow] | None,
                                                    dict[str, Any] | None]:
    """Read a PDS3 index label and its table, reporting a bad one rather than raising.

    Parameters:
        ctx: The import run's context, for the arguments and the logger.
        filename: The index label file.

    Returns:
        The rows and the label as a dictionary, or ``(None, None)`` if reading raised an
        exception or produced Python warnings. Either way the failure is logged, which
        marks the import as having produced bad data.
    """
    preprocess_label_func = None
    preprocess_table_func = None
    # for (set_search, set_preprocess_label,
    #      set_preprocess_table) in instruments.PDSTABLE_PREPROCESS:
    #     if re.fullmatch(set_search, filename.upper()):
    #         preprocess_label_func = set_preprocess_label
    #         preprocess_table_func = set_preprocess_table

    replacements = {}
    for set_search, set_replacements in instruments.PDSTABLE_REPLACEMENTS:
        if re.fullmatch(set_search, filename.upper()):
            replacements = set_replacements
            break
    try:
        if preprocess_label_func is None:
            table = pdstable.PdsTable(filename, replacements=replacements,
                                      table_callback=preprocess_table_func)
        else:
            lines = pdsparser.PdsLabel.load_file(filename)
            lines = preprocess_label_func(lines)
            table = pdstable.PdsTable(filename, label_contents=lines,
                                      replacements=replacements,
                                      table_callback=preprocess_table_func)

    except KeyboardInterrupt:
        raise
    except Exception:
        msg = f'Exception during reading of "{filename}"'
        if not ctx.args.log_suppress_traceback:
            msg += ':\n' + traceback.format_exc()
        log_error(ctx, msg)
        return None, None

    if log_accumulated_warnings(ctx, f'table import of {filename}'):
        return None, None

    rows = table.dicts_by_row()
    label = table.info.label.as_dict()

    return rows, label

def safe_column(row: IndexRow, column_name: str, idx: int | None = None) -> Any:
    """Read a value from a pdstable column accounting for the mask.

    Parameters:
        row: One row keyed by column name -- an index row, or a row the import has
            already computed.
        column_name: The column to read.
        idx: Which element to read from a column that holds a sequence, or None to read
            the whole column value.

    Returns:
        The value, or None if the column is absent from the row or the table's mask
        marks it as missing. A masked element makes only that element None; a mask with
        any element set makes the whole column None when ``idx`` is None.
    """
    if column_name not in row:
        return None

    if column_name+'_mask' not in row:
        if idx is None:
            return row[column_name]
        return row[column_name][idx]

    if idx is None:
        if np.any(row[column_name+'_mask']):
            return None
        return row[column_name]

    if row[column_name+'_mask'][idx]:
        return None
    return row[column_name][idx]


################################################################################
# TABLE MANIPULATION
################################################################################

def table_name_obs_mission(mission_name: str) -> str:
    """Return the name of a mission's own observation table.

    Parameters:
        mission_name: The OPUS mission id, such as ``'CO'``.

    Returns:
        The table name, such as ``'obs_mission_cassini'``.
    """
    assert mission_name in config_data.MISSION_ID_TO_MISSION_TABLE_SFX
    return ('obs_mission_'+
            config_data.MISSION_ID_TO_MISSION_TABLE_SFX[mission_name].lower())

def table_name_obs_instrument(inst_name: str) -> str:
    """Return the name of an instrument's own observation table.

    Parameters:
        inst_name: The OPUS instrument id, such as ``'COISS'``.

    Returns:
        The table name, such as ``'obs_instrument_coiss'``.
    """
    assert inst_name in config_data.INSTRUMENT_ID_TO_MISSION_ID
    return 'obs_instrument_'+inst_name.lower()

def table_name_mult(table_name: str, field_name: str) -> str:
    """Return the name of the ``mult_`` table holding one column's enumerated values.

    Parameters:
        table_name: The observation table the column belongs to.
        field_name: The column.

    Returns:
        The table name, such as ``'mult_obs_general_planet_id'``.
    """
    return 'mult_'+table_name.lower()+'_'+field_name.lower()

# These two have no caller anywhere in the repository, and could never have had one:
# both read `impglobals.DATABASES`, an attribute that never existed (the global was
# `DATABASE`), so either would have raised AttributeError on its first call. They are
# threaded rather than deleted because deleting unused code belongs to the dead-code PR,
# and the context spelling is what the name obviously meant.
def table_name_param_info(ctx: ImportContext, namespace: Namespace) -> str:
    """Return the name of the ``param_info`` table in a namespace.

    Parameters:
        ctx: The import run's context, for the open database.
        namespace: The namespace to name the table in.

    Returns:
        The table name, prefixed if the namespace is the import one.
    """
    assert ctx.db is not None
    return ctx.db.convert_raw_to_namespace(namespace, 'param_info')

def table_name_partables(ctx: ImportContext, namespace: Namespace) -> str:
    """Return the name of the ``partables`` table in a namespace.

    Parameters:
        ctx: The import run's context, for the open database.
        namespace: The namespace to name the table in.

    Returns:
        The table name, prefixed if the namespace is the import one.
    """
    assert ctx.db is not None
    return ctx.db.convert_raw_to_namespace(namespace, 'partables')

def encode_target_name(target_name: str) -> str:
    """Return a target name in the form a surface geometry table name uses.

    Parameters:
        target_name: The target name as a PDS label spells it.

    Returns:
        The name lowercased, with each ``/`` replaced by three underscores and each
        space by four, so the result is a legal SQL identifier that
        `decode_target_name` can turn back into the original.
    """
    target_name = target_name.lower()
    target_name = target_name.replace('/', '___')
    target_name = target_name.replace(' ', '____')
    return target_name

def decode_target_name(target_name: str) -> str:
    """Return the target name an encoded surface geometry table name was made from.

    Parameters:
        target_name: The encoded name.

    Returns:
        The name with the underscore runs turned back into spaces and slashes. The
        lowercasing `encode_target_name` did is not undone.
    """
    target_name = target_name.replace('____', ' ')
    target_name = target_name.replace('___', '/')
    return target_name

def table_name_for_sfc_target(target_name: str) -> str:
    """Return the encoded target name a surface geometry table is named for.

    Parameters:
        target_name: The target name as a PDS label spells it.

    Returns:
        The encoded form of the target's canonical name, after applying the alias
        mapping that folds a label's spelling onto the name OPUS uses.
    """
    if target_name.upper() in config_targets.TARGET_NAME_MAPPING:
        target_name = config_targets.TARGET_NAME_MAPPING[target_name.upper()]
    return encode_target_name(target_name)

# NOTE: whenever we change this function, we will have to change
# getSurfacegeoTargetSlug in JS code (in utils.js) as well.
def slug_name_for_sfc_target(target_name: str) -> str:
    """Return the slug a surface geometry target's search parameters are named with.

    Parameters:
        target_name: The target name as a PDS label spells it.

    Returns:
        The target's canonical name lowercased with every underscore, slash and space
        removed, which is what the web application's slugs embed.
    """
    if target_name.upper() in config_targets.TARGET_NAME_MAPPING:
        target_name = config_targets.TARGET_NAME_MAPPING[target_name.upper()]
    target_name = target_name.lower()
    target_name = target_name.replace('_', '').replace('/', '').replace(' ', '')
    return target_name

def table_schema_files(pattern: str) -> list[Traversable]:
    """Return the packaged table_schemas files whose names match a glob pattern.

    Parameters:
        pattern: An `fnmatch` pattern matched against the file name alone, such as
            ``obs*.json``.

    Returns:
        The matching files, sorted by name, as importlib.resources traversables. Sorting
        makes an import run's order independent of the file system's directory order.
    """
    return sorted((entry for entry in TABLE_SCHEMA_DIR.iterdir()
                   if entry.is_file() and fnmatch.fnmatch(entry.name, pattern)),
                  key=lambda entry: entry.name)

def read_schema_for_table(ctx: ImportContext, table_name: str,
                          replace: Sequence[tuple[str, str]] | None = None
                          ) -> TableSchema | None:
    """Read the packaged JSON schema that defines one OPUS table.

    Parameters:
        ctx: The import run's context, for the logger.
        table_name: The table. An import prefix is stripped, and the name is lowercased.
        replace: Text substitutions to apply to the schema before parsing it, as
            ``(from, to)`` pairs.

    Returns:
        The column definitions in the order the schema lists them, or None if there is
        no schema file of that name.

    Raises:
        json.decoder.JSONDecodeError: If the schema is not valid JSON. The table being
            read is logged first, since the parser's own message names no file.
    """
    table_name = table_name.replace(get_config().import_.table_temp_prefix, '').lower()
    if table_name.startswith('obs_surface_geometry__'):
        assert not replace
        target_name = table_name.replace('obs_surface_geometry__', '')
        table_name = 'obs_surface_geometry_target'
        replace = [('<TARGET>', table_name_for_sfc_target(target_name)),
                   ('<SLUGTARGET>', slug_name_for_sfc_target(target_name))]
    schema_file = TABLE_SCHEMA_DIR / (table_name+'.json')
    if not schema_file.is_file():
        return None
    contents = schema_file.read_text(encoding='utf-8')
    try:
        if replace:
            for r in replace:
                contents = contents.replace(r[0], r[1])
        schema: TableSchema = json.loads(contents)
        return schema
    except json.decoder.JSONDecodeError:
        log_debug(ctx, f'Was reading table "{table_name}"')
        raise

def find_max_table_id(ctx: ImportContext, table_name: str) -> Any:
    """Return the largest row id a table holds in either namespace.

    Parameters:
        ctx: The import run's context, for the open database.
        table_name: The table, without its namespace prefix.

    Returns:
        The larger of the two namespaces' maxima, or -1 if the table exists in neither
        or is empty in both.
    """
    assert ctx.db is not None
    max1 = -1
    max2 = -1
    if ctx.db.table_exists('import', table_name):
        max1 = ctx.db.find_column_max('import', table_name, 'id')
    if ctx.db.table_exists('perm', table_name):
        max2 = ctx.db.find_column_max('perm', table_name, 'id')
    if max1 is None and max2 is None:
        return -1
    if max1 is None:
        return max2
    if max2 is None:
        return max1
    return max(max1, max2)


################################################################################
# ANNOUNCE ERRORS BUT LET IMPORT CONTINUE
################################################################################

class NoDupLogger:
    """Wrapper around PdsLogger that only logs each message one time.

    This is used for logging of PdsFile warnings that we don't want to see
    over and over. An import run produces hundreds of thousands of these, so
    the record of what has been logged is a set: as a list it was scanned
    linearly on every call, and it never shrinks."""

    # Keyed by the repr of (msg, args, kwargs) rather than by the arguments
    # themselves, because kwargs is a dict and a caller's args need not be
    # hashable, so the tuple cannot go in a set directly. The record is
    # class-level and deliberately shared by every instance and never cleared:
    # the point is to log a given message once per process.
    _LOGGED_DEBUG: ClassVar[set[str]] = set()
    _LOGGED_WARN: ClassVar[set[str]] = set()
    _LOGGED_ERROR: ClassVar[set[str]] = set()
    _LOGGED_FATAL: ClassVar[set[str]] = set()

    def __init__(self, logger: pdslogger.PdsLogger) -> None:
        """Wrap a logger.

        Parameters:
            logger: The logger each first occurrence is passed to.
        """
        self._logger = logger

    def __getattr__(self, name: str) -> Any:
        """Return an attribute of the wrapped logger.

        Only the four level methods below are deduplicated; everything else the caller
        reaches is the wrapped logger's own.

        Parameters:
            name: The attribute to read.

        Returns:
            The wrapped logger's attribute of that name.
        """
        return getattr(self._logger, name)

    @staticmethod
    def _dedup_key(msg: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        """Return the key that decides whether two calls are the same message.

        Parameters:
            msg: The message.
            args: The positional arguments after it.
            kwargs: The keyword arguments.

        Returns:
            A string standing for all three. It is a repr rather than the values
            themselves because a caller's arguments need not be hashable.
        """
        return repr((msg, args, sorted(kwargs.items())))

    def _log_once(self, logged: set[str], log_func: Callable[..., None], msg: str,
                  args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        """Log a message unless this record has already seen it.

        Parameters:
            logged: The record of what this level has already logged, added to here.
            log_func: The wrapped logger's method for this level.
            msg: The message.
            args: The positional arguments after it.
            kwargs: The keyword arguments.
        """
        key = self._dedup_key(msg, args, kwargs)
        if key in logged:
            return
        logged.add(key)
        log_func(msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log at debug level, the first time this process is given this message.

        Parameters:
            msg: The message.
            args: Further positional arguments for the wrapped logger.
            kwargs: Further keyword arguments for the wrapped logger.
        """
        self._log_once(self._LOGGED_DEBUG, self._logger.debug, msg, args, kwargs)

    def warn(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log at warning level, the first time this process is given this message.

        Parameters:
            msg: The message.
            args: Further positional arguments for the wrapped logger.
            kwargs: Further keyword arguments for the wrapped logger.
        """
        self._log_once(self._LOGGED_WARN, self._logger.warn, msg, args, kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log at error level, the first time this process is given this message.

        Parameters:
            msg: The message.
            args: Further positional arguments for the wrapped logger.
            kwargs: Further keyword arguments for the wrapped logger.
        """
        self._log_once(self._LOGGED_ERROR, self._logger.error, msg, args, kwargs)

    def fatal(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log at fatal level, the first time this process is given this message.

        Parameters:
            msg: The message.
            args: Further positional arguments for the wrapped logger.
            kwargs: Further keyword arguments for the wrapped logger.
        """
        self._log_once(self._LOGGED_FATAL, self._logger.fatal, msg, args, kwargs)

# The step modules log through these; the obs classes reach the same operations as
# `self._ctx.log.<name>`. Both spellings are one implementation, on `ImportLog`.

def log_error(ctx: ImportContext, msg: str, *args: Any) -> None:
    """Log a message at error level and mark the import as having produced bad data.

    Parameters:
        ctx: The import run's context.
        msg: The message, position-prefixed before it is logged.
        args: Further arguments passed to the underlying logger.
    """
    ctx.log.error(msg, *args)

def log_warning(ctx: ImportContext, msg: str, *args: Any) -> None:
    """Log a message at warning level.

    Parameters:
        ctx: The import run's context.
        msg: The message, position-prefixed before it is logged.
        args: Further arguments passed to the underlying logger.
    """
    ctx.log.warning(msg, *args)

def log_info(ctx: ImportContext, msg: str, *args: Any) -> None:
    """Log a message at info level.

    Parameters:
        ctx: The import run's context.
        msg: The message, position-prefixed before it is logged.
        args: Further arguments passed to the underlying logger.
    """
    ctx.log.info(msg, *args)

def log_debug(ctx: ImportContext, msg: str, *args: Any) -> None:
    """Log a message at debug level.

    Parameters:
        ctx: The import run's context.
        msg: The message, position-prefixed before it is logged.
        args: Further arguments passed to the underlying logger.
    """
    ctx.log.debug(msg, *args)

def log_nonrepeating_error(ctx: ImportContext, msg: str) -> None:
    """Log an error the first time this run produces it, and ignore it after that.

    Parameters:
        ctx: The import run's context.
        msg: The message.
    """
    ctx.log.nonrepeating_error(msg)

def log_nonrepeating_warning(ctx: ImportContext, msg: str) -> None:
    """Log a warning the first time this run produces it, and ignore it after that.

    Parameters:
        ctx: The import run's context.
        msg: The message.
    """
    ctx.log.nonrepeating_warning(msg)

def log_unknown_target_name(ctx: ImportContext, target_name: str) -> None:
    """Report a TARGET_NAME the target tables do not describe.

    Parameters:
        ctx: The import run's context.
        target_name: The name read from the PDS label.
    """
    ctx.log.unknown_target_name(target_name)


################################################################################
# MISC UTILITIES
################################################################################

@lru_cache(maxsize=64)
def cached_tai_from_iso(s: str) -> float:
    """Return the TAI seconds an ISO time string stands for, remembering recent answers.

    An index row's times repeat across the rows of one observation, so the last 64
    conversions are kept.

    Parameters:
        s: The time, in ISO format.

    Returns:
        Seconds past the J2000 epoch, in TAI.
    """
    tai: float = julian.tai_from_iso(s)
    return tai

def safe_join(*paths: str) -> str:
    """Join path components with forward slashes on every operating system.

    PDS filespecs are compared as text throughout the pipeline and on the web side, so a
    Windows backslash in one would not match the same path built anywhere else.

    Parameters:
        paths: The components to join.

    Returns:
        The joined path, with every backslash turned into a forward slash.
    """
    return os.path.join(*paths).replace('\\', '/')
