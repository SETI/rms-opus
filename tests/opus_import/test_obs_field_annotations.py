"""The obs hierarchy's annotations are checked against the schemas and against behavior.

Two layers, because either one alone can be satisfied by a mistake:

1. **Schema.** Every ``field_obs_<table>_<column>`` method is resolved against the
   packaged ``table_schemas`` JSON and its declared return type is required to be the
   alias `opus_import.obs.field_types` gives that column. This is what keeps the
   hierarchy and the schemas from drifting apart, in either direction: a method that
   answers to no column is a method the import can never call, and a column with no
   method is a column the import will fail on.
2. **Behavior.** One instrument class per mission is driven against a metadata fixture
   and every field method it resolves is called, with the value it returns checked
   against the alias it declares. A schema check alone cannot see that a method returns
   a string where its column says a number.

**What layer 2 does not cover, so nobody reads its green as more than it is.** It drives
6 of the 25 leaf classes in `opus_import.config_bundle_info`, whose method resolution
orders between them reach 27 of the 57 modules here: **669 of the 1185 field method
definitions, 56%, are in modules it cannot instantiate** -- the whole PDS4 branch and all
three ``obs_bundle_*`` leaves among them. A wrong runtime type in one of those is caught
by layer 1 only insofar as the schema can see it, which is not at all. Widening this is
what PR-19's fixture work is for; until then the honest claim is that layer 2 covers the
missions, not the hierarchy.

The decision table lives here rather than in the package because it is the test's
statement of what the annotations must be, not something the pipeline consults.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import textwrap
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from opus_import import config_data, obs
from opus_import.config_bundle_info import BUNDLE_INFO
from opus_import.obs.field_types import as_int
from opus_import.obs.obs_base import ObsBase

from .conftest import make_context

_OBS_DIR = Path(obs.__file__).parent
_SCHEMA_DIR = Path(config_data.__file__).parent / 'table_schemas'

#: The columns a geometry summary file holds are all floating-point, which is what lets
#: `_GeometryRow` stand in for one without naming any of them.
_GEOMETRY_VALUE = 12.5


def _alias_for(field_type: str | None, form_type: str | None) -> str | None:
    """Return the alias a schema column's field method must declare.

    The form type decides first: a column offered in the search form as a group stores
    an index into a ``mult_`` table whatever its storage type is, so its method returns
    a mult dictionary rather than a scalar.

    Parameters:
        field_type: The column's ``field_type``.
        form_type: The column's ``pi_form_type``, with or without its ``:`` suffix.

    Returns:
        The alias name, or None for a column no field method computes.
    """
    head = form_type.split(':')[0] if isinstance(form_type, str) else form_type
    if head == 'GROUP':
        return 'MultFieldRet'
    if head == 'MULTIGROUP':
        return 'list[MultField]'
    if field_type is None:
        return None
    if field_type.startswith(('char', 'varchar')) or field_type in ('text', 'json'):
        return 'StrField'
    if field_type.startswith('real'):
        return 'FloatField'
    if field_type.startswith(('int', 'uint')):
        return 'IntField'
    return None


def _schema_columns() -> dict[str, dict[str, Any]]:
    """Return every ``obs_`` table column, keyed by the method name that computes it."""
    columns = {}
    for path in sorted(_SCHEMA_DIR.glob('obs_*.json')):
        table = path.stem
        for column in json.loads(path.read_text(encoding='utf-8')):
            if not isinstance(column, dict) or column.get('field_name') is None:
                continue
            columns['field_' + table + '_' + column['field_name']] = column
    return columns


def _field_methods() -> list[tuple[str, str, str, int, str | None]]:
    """Return every field method defined in the hierarchy, read from its source.

    Returns:
        One ``(module, class, method, line, annotation)`` per definition, with the
        annotation as it is written rather than as it evaluates -- the check is that the
        source says the alias, which is what a reader of the module sees.
    """
    found = []
    for path in sorted(_OBS_DIR.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'), str(path))
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            for fn in cls.body:
                if not isinstance(fn, ast.FunctionDef):
                    continue
                if not fn.name.startswith('field_obs_'):
                    continue
                annotation = ast.unparse(fn.returns) if fn.returns is not None else None
                found.append((path.name, cls.name, fn.name, fn.lineno, annotation))
    return found


def _declared_annotations() -> dict[str, str]:
    """Return the alias each field method declares, keyed by method name.

    Returns:
        One entry per name. A name defined in several classes must declare the same
        alias in each, which layer 1 requires of them independently; this raises rather
        than choosing if that ever stops holding, since a caller here has no way to know
        which class it will resolve to.
    """
    declared: dict[str, str] = {}
    for module, cls, name, line, annotation in _field_methods():
        assert annotation is not None, f'{module}:{line} {cls}.{name}'
        if declared.setdefault(name, annotation) != annotation:
            raise AssertionError(
                f'{module}:{line} {cls}.{name} declares {annotation!r}, but another '
                f'class declares {declared[name]!r} for the same column')
    return declared


def _only_raises(method: Any) -> bool:
    """Whether a method's whole body is a raise, which an abstract stub's is.

    Read from the source rather than by calling it: an obs class's field methods reach
    the index, and a stub is exactly the case where there is nothing to reach.
    """
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
    except (OSError, TypeError, SyntaxError):  # pragma: no cover - not a Python method
        return False
    # tree.body[0] is the FunctionDef just parsed; ast.Module.body is not narrowed.
    body = [n for n in tree.body[0].body   # type: ignore[attr-defined]
            if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
    return len(body) == 1 and isinstance(body[0], ast.Raise)


def _leaf_classes() -> list[type[ObsBase]]:
    """Return every obs class `opus_import.config_bundle_info` can instantiate."""
    leaves: list[type[ObsBase]] = []
    for _pattern, info in BUNDLE_INFO:
        cls = info['instrument_class']
        if cls is not None and cls not in leaves:
            leaves.append(cls)
    return leaves


def _tables_for(instrument: ObsBase) -> list[str]:
    """Return the tables an instrument's bundle populates, as the import names them."""
    inst_id = instrument.instrument_id
    mission_name = config_data.MISSION_ID_TO_MISSION_TABLE_SFX[instrument.mission_id]
    tables = []
    for template in config_data.TABLES_TO_POPULATE:
        table = template
        if inst_id is not None:
            table = table.replace('<INST>', inst_id.lower())
        table = table.replace('<MISSION>', mission_name.lower())
        if table.startswith('obs_surface_geometry__'):
            # Every per-target surface geometry table is built from one template, which
            # is the table the field methods are named for.
            table = 'obs_surface_geometry_target'
        if (_SCHEMA_DIR / (table + '.json')).is_file():
            tables.append(table)
    return tables


# --- Layer 1: the annotations agree with the schemas ---------------------------------

def test_the_hierarchy_is_actually_being_read() -> None:
    """The source scan finds the methods, so the checks below are not vacuous.

    Every layer-1 check is a comparison against `_field_methods`, and each of them
    passes trivially if that returns nothing -- which a moved package, a renamed
    directory or a broken parse would all produce.
    """
    found = _field_methods()

    assert len(found) > 1000, f'only {len(found)} field methods found'
    assert len({module for module, _c, _n, _l, _a in found}) > 40


def test_every_field_method_answers_to_a_schema_column() -> None:
    """A method no column names is a method the import can never call.

    `opus_import.steps.do_import_obs.import_run_field_function` builds the name it looks
    up as ``field_`` plus the table plus the column, so a method whose name does not
    decompose that way is unreachable -- dead code, or a name with a typo in it.
    """
    columns = _schema_columns()
    orphans = [(module, cls, name) for module, cls, name, _line, _ann in _field_methods()
               if name not in columns]

    assert orphans == []


def test_every_field_method_is_annotated_from_its_schema_column() -> None:
    """The declared return type is the alias the column's schema entry calls for."""
    columns = _schema_columns()
    wrong = []
    for module, cls, name, line, annotation in _field_methods():
        column = columns[name]
        expected = _alias_for(column.get('field_type'), column.get('pi_form_type'))
        if annotation != expected:
            wrong.append(f'{module}:{line} {cls}.{name} declares {annotation!r}, '
                         f'schema calls for {expected!r}')

    assert wrong == []


def test_every_column_the_import_computes_has_a_field_method() -> None:
    """A column with no method fails the import for every observation in the bundle.

    Resolved through each leaf class's own method resolution order, because a bundle
    class inherits most of its columns and overrides a few.
    """
    columns = _schema_columns()
    missing = []
    for cls in _leaf_classes():
        instrument = cls(make_context(), bundle='TEST_BUNDLE')
        for table in _tables_for(instrument):
            for name, column in columns.items():
                if not name.startswith('field_' + table + '_'):
                    continue
                if column.get('data_source') != 'COMPUTE':
                    continue
                method = getattr(cls, name, None)
                if method is None:
                    missing.append(f'{cls.__name__} populates {table} but has no {name}')
                elif _only_raises(method):
                    # `hasattr` alone would be satisfied by an abstract stub, which the
                    # import cannot use: calling it aborts the column.
                    missing.append(
                        f'{cls.__name__} populates {table} but resolves {name} to a '
                        f'stub that only raises')

    assert missing == []


def test_the_decision_table_covers_every_column_the_import_computes() -> None:
    """No computed column falls through the table with no alias to check against."""
    uncovered = [name for name, column in _schema_columns().items()
                 if column.get('data_source') == 'COMPUTE'
                 and _alias_for(column.get('field_type'),
                                column.get('pi_form_type')) is None]

    assert uncovered == []


def test_a_group_column_is_decided_by_its_form_type_not_its_storage_type() -> None:
    """The rule that makes the table form-type-first, pinned against the schemas.

    A ``flag_yesno``, ``flag_onoff`` or ``char`` column carrying a GROUP form type is an
    index into a ``mult_`` table exactly like a ``mult_idx`` one, so reading the storage
    type instead would annotate its method as a scalar. This fails if a schema ever
    stops exercising that case, which would make the rule untested rather than wrong.
    """
    group_but_not_mult = {
        name: column['field_type'] for name, column in _schema_columns().items()
        if isinstance(column.get('pi_form_type'), str)
        and column['pi_form_type'].split(':')[0] in ('GROUP', 'MULTIGROUP')
        and column['field_type'] not in ('mult_idx', 'mult_list')}

    assert group_but_not_mult, 'no non-mult_idx column carries a group form type'
    for name, field_type in group_but_not_mult.items():
        assert _alias_for(field_type, 'GROUP') == 'MultFieldRet', name


# --- Layer 2: the values agree with the annotations -----------------------------------

#: The column names a real geometry summary file declares, measured across the 2738
#: ``*summary.lbl`` files in the RMS holdings -- every one of them ``ASCII_REAL``, which
#: is why `opus_import.obs.obs_base.ObsBase._ring_geo_index_col` and its two siblings
#: can declare a float. Regenerate with a scan of
#: ``holdings/metadata/**/*summary.lbl`` for ``NAME``/``DATA_TYPE`` pairs.
#:
#: This is a vocabulary, not a whitelist of what the code may ask for: the obs classes
#: deliberately probe alternate spellings through the ``col2``/``col3`` fallbacks, for
#: older and newer generations of these files, and a name outside this set simply reads
#: as absent -- which is exactly what it would do against a bundle whose summary file
#: does not carry it.
_GEOMETRY_COLUMNS = frozenset((
    'CENTER_DISTANCE', 'CENTER_PHASE_ANGLE', 'CENTER_RESOLUTION',
    'COARSEST_EDGE_ON_RADIAL_RESOLUTION', 'COARSEST_RADIAL_RESOLUTION',
    'COARSEST_RING_INTERCEPT_RESOLUTION', 'FINEST_EDGE_ON_RADIAL_RESOLUTION',
    'FINEST_RADIAL_RESOLUTION', 'FINEST_RING_INTERCEPT_RESOLUTION',
    'MAXIMUM_CENTER_DISTANCE', 'MAXIMUM_CENTER_PHASE_ANGLE',
    'MAXIMUM_CENTER_RESOLUTION', 'MAXIMUM_COARSEST_SURFACE_RESOLUTION',
    'MAXIMUM_DECLINATION', 'MAXIMUM_EDGE_ON_INTERCEPT_DISTANCE',
    'MAXIMUM_EDGE_ON_RING_ALTITUDE', 'MAXIMUM_EDGE_ON_RING_LONGITUDE',
    'MAXIMUM_EDGE_ON_RING_LONGITUDE_WRT_NODE', 'MAXIMUM_EDGE_ON_RING_RADIUS',
    'MAXIMUM_EDGE_ON_SOLAR_HOUR_ANGLE', 'MAXIMUM_EMISSION_ANGLE',
    'MAXIMUM_FINEST_SURFACE_RESOLUTION', 'MAXIMUM_IAU_LONGITUDE',
    'MAXIMUM_IAU_LONGITUDE_EAST', 'MAXIMUM_INCIDENCE_ANGLE',
    'MAXIMUM_LOCAL_HOUR_ANGLE', 'MAXIMUM_LONGITUDE_WRT_OBSERVER',
    'MAXIMUM_LONGITUDE_WRT_OBSERVER_EAST', 'MAXIMUM_NORTH_BASED_EMISSION_ANGLE',
    'MAXIMUM_NORTH_BASED_INCIDENCE_ANGLE', 'MAXIMUM_OBSERVER_RING_ELEVATION',
    'MAXIMUM_OBSERVER_RING_OPENING', 'MAXIMUM_OBSERVER_RING_OPENING_ANGLE',
    'MAXIMUM_PHASE_ANGLE', 'MAXIMUM_PLANETOCENTRIC_LATITUDE',
    'MAXIMUM_PLANETOGRAPHIC_LATITUDE', 'MAXIMUM_RIGHT_ASCENSION',
    'MAXIMUM_RING_AZIMUTH', 'MAXIMUM_RING_CENTER_DISTANCE',
    'MAXIMUM_RING_CENTER_EMISSION_ANGLE', 'MAXIMUM_RING_CENTER_INCIDENCE_ANGLE',
    'MAXIMUM_RING_CENTER_NORTH_BASED_EMISSION_ANGLE',
    'MAXIMUM_RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE',
    'MAXIMUM_RING_CENTER_PHASE_ANGLE', 'MAXIMUM_RING_DISTANCE',
    'MAXIMUM_RING_EMISSION_ANGLE', 'MAXIMUM_RING_INCIDENCE_ANGLE',
    'MAXIMUM_RING_LONGITUDE', 'MAXIMUM_RING_LONGITUDE_WRT_NODE',
    'MAXIMUM_RING_LONGITUDE_WRT_OBSERVER', 'MAXIMUM_RING_PHASE_ANGLE',
    'MAXIMUM_RING_RADIUS', 'MAXIMUM_SOLAR_HOUR_ANGLE',
    'MAXIMUM_SOLAR_RING_ELEVATION', 'MAXIMUM_SOLAR_RING_OPENING',
    'MAXIMUM_SOLAR_RING_OPENING_ANGLE', 'MAXIMUM_SUB_OBSERVER_IAU_LONGITUDE',
    'MAXIMUM_SUB_OBSERVER_PLANETOCENTRIC_LATITUDE',
    'MAXIMUM_SUB_OBSERVER_PLANETOGRAPHIC_LATITUDE',
    'MAXIMUM_SUB_OBSERVER_RING_LONGITUDE', 'MAXIMUM_SUB_SOLAR_IAU_LONGITUDE',
    'MAXIMUM_SUB_SOLAR_PLANETOCENTRIC_LATITUDE',
    'MAXIMUM_SUB_SOLAR_PLANETOGRAPHIC_LATITUDE', 'MAXIMUM_SUB_SOLAR_RING_LONGITUDE',
    'MAXIMUM_SURFACE_DISTANCE', 'MINIMUM_CENTER_DISTANCE',
    'MINIMUM_CENTER_PHASE_ANGLE', 'MINIMUM_CENTER_RESOLUTION',
    'MINIMUM_COARSEST_SURFACE_RESOLUTION', 'MINIMUM_DECLINATION',
    'MINIMUM_EDGE_ON_INTERCEPT_DISTANCE', 'MINIMUM_EDGE_ON_RING_ALTITUDE',
    'MINIMUM_EDGE_ON_RING_LONGITUDE', 'MINIMUM_EDGE_ON_RING_LONGITUDE_WRT_NODE',
    'MINIMUM_EDGE_ON_RING_RADIUS', 'MINIMUM_EDGE_ON_SOLAR_HOUR_ANGLE',
    'MINIMUM_EMISSION_ANGLE', 'MINIMUM_FINEST_SURFACE_RESOLUTION',
    'MINIMUM_IAU_LONGITUDE', 'MINIMUM_IAU_LONGITUDE_EAST',
    'MINIMUM_INCIDENCE_ANGLE', 'MINIMUM_LOCAL_HOUR_ANGLE',
    'MINIMUM_LONGITUDE_WRT_OBSERVER', 'MINIMUM_LONGITUDE_WRT_OBSERVER_EAST',
    'MINIMUM_NORTH_BASED_EMISSION_ANGLE', 'MINIMUM_NORTH_BASED_INCIDENCE_ANGLE',
    'MINIMUM_OBSERVER_RING_ELEVATION', 'MINIMUM_OBSERVER_RING_OPENING',
    'MINIMUM_OBSERVER_RING_OPENING_ANGLE', 'MINIMUM_PHASE_ANGLE',
    'MINIMUM_PLANETOCENTRIC_LATITUDE', 'MINIMUM_PLANETOGRAPHIC_LATITUDE',
    'MINIMUM_RIGHT_ASCENSION', 'MINIMUM_RING_AZIMUTH',
    'MINIMUM_RING_CENTER_DISTANCE', 'MINIMUM_RING_CENTER_EMISSION_ANGLE',
    'MINIMUM_RING_CENTER_INCIDENCE_ANGLE',
    'MINIMUM_RING_CENTER_NORTH_BASED_EMISSION_ANGLE',
    'MINIMUM_RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE',
    'MINIMUM_RING_CENTER_PHASE_ANGLE', 'MINIMUM_RING_DISTANCE',
    'MINIMUM_RING_EMISSION_ANGLE', 'MINIMUM_RING_INCIDENCE_ANGLE',
    'MINIMUM_RING_LONGITUDE', 'MINIMUM_RING_LONGITUDE_WRT_NODE',
    'MINIMUM_RING_LONGITUDE_WRT_OBSERVER', 'MINIMUM_RING_PHASE_ANGLE',
    'MINIMUM_RING_RADIUS', 'MINIMUM_SOLAR_HOUR_ANGLE',
    'MINIMUM_SOLAR_RING_ELEVATION', 'MINIMUM_SOLAR_RING_OPENING',
    'MINIMUM_SOLAR_RING_OPENING_ANGLE', 'MINIMUM_SUB_OBSERVER_IAU_LONGITUDE',
    'MINIMUM_SUB_OBSERVER_PLANETOCENTRIC_LATITUDE',
    'MINIMUM_SUB_OBSERVER_PLANETOGRAPHIC_LATITUDE',
    'MINIMUM_SUB_OBSERVER_RING_LONGITUDE', 'MINIMUM_SUB_SOLAR_IAU_LONGITUDE',
    'MINIMUM_SUB_SOLAR_PLANETOCENTRIC_LATITUDE',
    'MINIMUM_SUB_SOLAR_PLANETOGRAPHIC_LATITUDE', 'MINIMUM_SUB_SOLAR_RING_LONGITUDE',
    'MINIMUM_SURFACE_DISTANCE', 'OBSERVER_RING_OPENING_ANGLE',
    'RING_CENTER_DISTANCE', 'RING_CENTER_EMISSION_ANGLE',
    'RING_CENTER_INCIDENCE_ANGLE', 'RING_CENTER_NORTH_BASED_EMISSION_ANGLE',
    'RING_CENTER_NORTH_BASED_INCIDENCE_ANGLE', 'RING_CENTER_PHASE_ANGLE',
    'SOLAR_RING_OPENING_ANGLE', 'SUB_OBSERVER_IAU_LONGITUDE',
    'SUB_OBSERVER_IAU_LONGITUDE_EAST', 'SUB_OBSERVER_PLANETOCENTRIC_LATITUDE',
    'SUB_OBSERVER_PLANETOGRAPHIC_LATITUDE', 'SUB_OBSERVER_RING_LONGITUDE',
    'SUB_OBSERVER_RING_LONGITUDE_WRT_NODE', 'SUB_SOLAR_IAU_LONGITUDE',
    'SUB_SOLAR_IAU_LONGITUDE_EAST', 'SUB_SOLAR_PLANETOCENTRIC_LATITUDE',
    'SUB_SOLAR_PLANETOGRAPHIC_LATITUDE', 'SUB_SOLAR_RING_LONGITUDE',
    'SUB_SOLAR_RING_LONGITUDE_WRT_NODE'
))


class _GeometryRow(dict[str, Any]):
    """A geometry summary row carrying the columns a real one declares, as floats.

    Answering to any name at all would make this layer blind to the mistake it most
    needs to catch: a geometry column renamed or misspelled in an obs class would still
    read back a number, and every count would be unchanged. Only
    `_GEOMETRY_COLUMNS` answers; anything else reads as absent.

    Mask columns are deliberately absent, which is how
    `opus_import.import_util.safe_column` reads a row whose values are all present.
    """

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key in _GEOMETRY_COLUMNS

    def __getitem__(self, key: str) -> Any:
        if key not in _GEOMETRY_COLUMNS:
            raise KeyError(key)
        return _GEOMETRY_VALUE


class _FakePdsFile:
    """The `pdsfile` object an obs class asks for, without any holdings to read."""

    opus_id = 'co-iss-n1294561143'
    logical_path = 'volumes/COISS_2xxx/COISS_2002/data/1294561143_1295221348/N1294561143_1.IMG'
    viewset = None


#: What each mission's representative bundle looks like to the obs classes: the primary
#: index row, the supplemental index row, and the index label. Values are the shapes the
#: real indexes carry -- a time is an ISO string, a spacecraft clock count is that
#: mission's own text format -- because the point of the layer is to drive the parsing.
_MISSION_FIXTURES: dict[str, dict[str, Any]] = {
    'COISS': {
        'class_name': 'ObsVolumeCOISS12xxx',
        'index_row': {
            'FILE_SPECIFICATION_NAME': 'data/1294561143_1295221348/N1294561143_1.LBL',
            'FILE_NAME': 'N1294561143_1.LBL',
            'INSTRUMENT_ID': 'ISSNA',
            'DATA_SET_ID': 'CO-S-ISSNA/ISSWA-2-EDR-V1.0',
            'PRODUCT_ID': 'N1294561143_1.IMG',
            'PRODUCT_CREATION_TIME': '2005-05-02T12:00:00.000',
            'START_TIME': '2005-01-01T00:00:00.000',
            'STOP_TIME': '2005-01-01T00:00:10.000',
            'EARTH_RECEIVED_START_TIME': '2005-01-02T00:00:00.000',
            'EARTH_RECEIVED_STOP_TIME': '2005-01-02T00:00:10.000',
            'SPACECRAFT_CLOCK_CNT_PARTITION': 1,
            'SPACECRAFT_CLOCK_START_COUNT': '1294561143.125',
            'SPACECRAFT_CLOCK_STOP_COUNT': '1294561153.125',
            'TARGET_NAME': 'SATURN',
            'TARGET_DESC': 'SATURN',
            'OBSERVATION_ID': 'ISS_00ASA_MOONSWATCH001_PRIME',
            'IMAGE_NUMBER': '1294561143',
            'IMAGE_OBSERVATION_TYPE': 'SCIENCE',
            'INSTRUMENT_MODE_ID': 'FULL',
            'DATA_CONVERSION_TYPE': '12BIT',
            'INST_CMPRS_TYPE': 'LOSSLESS',
            'GAIN_MODE_ID': '12 ELECTRONS PER DN',
            'SHUTTER_MODE_ID': 'NACONLY',
            'SHUTTER_STATE_ID': 'ENABLED',
            'MISSING_LINES': 0,
            'FILTER_NAME': ('CL1', 'CL2'),
            'EXPOSURE_DURATION': 1200.0,
            'RIGHT_ASCENSION': 45.0,
            'DECLINATION': -12.5,
            'SEQUENCE_ID': 'S01',
            'DESCRIPTION': 'N/A',
        },
        'supp_index_row': {'PRODUCT_CREATION_TIME': '2005-05-02T12:00:00.000'},
    },
    'GOSSI': {
        'class_name': 'ObsVolumeGO0xxx',
        'index_row': {
            'FILE_SPECIFICATION_NAME': 'C0349632000R.LBL',
            'DATA_SET_ID': 'GO-J/JSA-SSI-2-REDR-V1.0',
            'PRODUCT_ID': 'C0349632000R.IMG',
            'PRODUCT_CREATION_TIME': '1997-01-01T00:00:00.000',
            'OBSERVATION_ID': 'C0349632000R',
            'IMAGE_ID': '0349632000',
            'MINIMUM_IMAGE_ID': '0349632000',
            'MAXIMUM_IMAGE_ID': '0349632000',
            'MINIMUM_IMAGE_TIME': '1996-06-26T00:00:00.000',
            'MAXIMUM_IMAGE_TIME': '1996-06-26T00:00:10.000',
            'TARGET_NAME': 'JUPITER',
            'FILTER_NAME': 'CLEAR',
            'FILTER_NUMBER': 0,
            'GAIN_MODE_ID': '400K',
            'FRAME_DURATION': 2.333,
            'COMPRESSION_TYPE': 'BARC',
            'OBSTRUCTION_ID': 'NONE',
            'ORBIT_NUMBER': 'G1',
            'EXPOSURE_DURATION': 195.0,
            'RIGHT_ASCENSION': 200.0,
            'DECLINATION': 5.0,
            'SPACECRAFT_CLOCK_START_COUNT': '03496:32:000',
            'PROCESSING_HISTORY_TEXT': 'GALSOS',
        },
        'supp_index_row': {
            'START_TIME': '1996-06-26T00:00:00.000',
            'STOP_TIME': '1996-06-26T00:00:10.000',
            'PRODUCT_CREATION_TIME': '1997-01-01T00:00:00.000',
            'SPACECRAFT_CLOCK_START_COUNT': '03496:32:000',
            'SPACECRAFT_CLOCK_STOP_COUNT': '03496:32:100',
            'CUT_OUT_WINDOW': (1, 1, 800, 800),
        },
    },
    'HSTWFPC2': {
        'class_name': 'ObsVolumeHSTUxxxxx',
        'index_row': {
            'FILE_SPECIFICATION_NAME': 'DATA/VISIT_01/U2NO0102T.LBL',
            'DATA_SET_ID': 'HST-S-WFPC2-2-EDR-V1.0',
            'PRODUCT_ID': 'U2NO0102T',
            'PRODUCT_CREATION_TIME': '1996-01-01T00:00:00.000',
            'START_TIME': '1995-08-13T00:00:00.000',
            'STOP_TIME': '1995-08-13T00:00:10.000',
            'TARGET_NAME': 'SATURN',
            'INSTRUMENT_ID': 'WFPC2',
            'DETECTOR_ID': 'PC1',
            'FILTER_NAME': 'F439W',
            'APERTURE_TYPE': 'PC1',
            'PROPOSED_APERTURE_TYPE': 'PC1',
            'EXPOSURE_DURATION': 100.0,
            'GAIN_MODE_ID': 'A2D7',
            'OBSERVATION_ID': 'U2NO0102T',
            'FINE_GUIDANCE_SYSTEM_LOCK_TYPE': 'FINE',
            'HST_PROPOSAL_ID': 6030,
            'HST_PI_NAME': 'KARKOSCHKA, ERICH',
            'HST_TARGET_NAME': 'SATURN',
            'PUBLICATION_DATE': '1996-08-13',
            'RIGHT_ASCENSION': 330.0,
            'DECLINATION': -12.0,
            'ORIENTATION': 100.0,
            'BANDWIDTH': 473.0,
            'CENTER_FILTER_WAVELENGTH': 4300.0,
            'TARGETED_DETECTOR_ID': 'PC1',
            'LINES': 800,
            'LINE_SAMPLES': 800,
        },
        'supp_index_row': {},
    },
    'NHLORRI': {
        'class_name': 'ObsVolumeNHxxLOXxxx',
        'index_row': {
            'PATH_NAME': 'data/20070108_003059',
            'FILE_NAME': 'lor_0030597859_0x630_eng.lbl',
            'FILE_SPECIFICATION_NAME':
                'data/20070108_003059/lor_0030597859_0x630_eng.lbl',
            'DATA_SET_ID': 'NH-J-LORRI-2-JUPITER-V1.0',
            'PRODUCT_ID': 'LOR_0030597859',
            'PRODUCT_CREATION_TIME': '2008-01-01T00:00:00.000',
            'START_TIME': '2007-01-08T00:30:59.000',
            'STOP_TIME': '2007-01-08T00:31:09.000',
            'TARGET_NAME': 'JUPITER',
            'MISSION_PHASE_NAME': 'JUPITER ENCOUNTER',
            'SPACECRAFT_CLOCK_START_COUNT': '1/0030597859:00000',
            'SPACECRAFT_CLOCK_STOP_COUNT': '1/0030597869:00000',
            'EXPOSURE_DURATION': 0.075,
            'INSTRUMENT_COMPRESSION_TYPE': 'LOSSLESS',
            'RIGHT_ASCENSION': 190.0,
            'DECLINATION': -3.0,
            'SEQUENCE_ID': 'LOR_0030597859',
            'OBSERVATION_DESC': 'Jupiter ring observation',
        },
        'supp_index_row': {
            'MISSION_PHASE_NAME': 'JUPITER ENCOUNTER',
            'SPACECRAFT_CLOCK_COUNT_PARTITION': 1,
            'SPACECRAFT_CLOCK_START_COUNT': '1/0030597859:00000',
            'SPACECRAFT_CLOCK_STOP_COUNT': '1/0030597869:00000',
            'START_TIME': '2007-01-08T00:30:59.000',
            'BINNING_MODE': '1X1',
            'INSTRUMENT_COMPRESSION_TYPE': 'LOSSLESS',
            'OBSERVATION_DESC': 'Jupiter ring observation',
            'EXPOSURE_DURATION': 0.075,
            'MINIMUM_RIGHT_ASCENSION': 189.0,
            'MAXIMUM_RIGHT_ASCENSION': 191.0,
            'MINIMUM_DECLINATION': -4.0,
            'MAXIMUM_DECLINATION': -2.0,
        },
    },
    'VGISS': {
        'class_name': 'ObsVolumeVGISS5678xxx',
        'index_row': {
            'FILE_SPECIFICATION_NAME': 'DATA/C13854XX/C1385455_RAW.LBL',
            'DATA_SET_ID': 'VG2-SR/UR/NR-ISS-2-EDR-V1.0',
            'PRODUCT_ID': 'C1385455_RAW.IMG',
            'PRODUCT_CREATION_TIME': '1999-01-01T00:00:00.000',
            'IMAGE_TIME': '1981-08-25T00:00:00.000',
            'EARTH_RECEIVED_TIME': '1981-08-25T02:00:00.000',
            'TARGET_NAME': 'SATURN',
            'INSTRUMENT_NAME': 'NARROW ANGLE CAMERA',
            'INSTRUMENT_HOST_NAME': 'VOYAGER 2',
            'FILTER_NAME': 'CLEAR',
            'FILTER_NUMBER': 0,
            'GAIN_MODE_ID': 'LOW',
            'EDIT_MODE_ID': '1:1',
            'SCAN_MODE_ID': '1:1',
            'SHUTTER_MODE_ID': 'NAONLY',
            'EXPOSURE_DURATION': 1.92,
            'IMAGE_NUMBER': '1385455',
            'MISSION_PHASE_NAME': 'SATURN ENCOUNTER',
            'SPACECRAFT_CLOCK_START_COUNT': '38545:55:001',
            'SPACECRAFT_CLOCK_STOP_COUNT': '38545:57:001',
            'NOTE': 'N/A',
        },
        'supp_index_row': {
            'INSTRUMENT_HOST_NAME': 'VOYAGER 2',
            'FIRST_LINE': 1,
            'LAST_LINE': 800,
            'FIRST_SAMPLE': 1,
            'LAST_SAMPLE': 800,
        },
    },
    'eso-la_silla.1m04': {
        'class_name': 'ObsVolumeEBROCCxxxx',
        'index_row': {
            'FILE_SPECIFICATION_NAME': 'DATA/ESO1M/ES1_EPD.LBL',
            'DATA_SET_ID': 'EBROCC-SR/UR/NR-RSS-4-OCC-V1.0',
            'PRODUCT_ID': 'ES1_EPD.TAB',
            'PRODUCT_CREATION_TIME': '1998-01-01T00:00:00.000',
            'START_TIME': '1989-07-03T00:00:00.000',
            'STOP_TIME': '1989-07-03T04:00:00.000',
            'TARGET_NAME': 'S RINGS',
            'INSTRUMENT_HOST_NAME': 'EUROPEAN SOUTHERN OBSERVATORY 1M TELESCOPE',
            'INSTRUMENT_NAME': 'INFRARED PHOTOMETER',
            'WAVELENGTH': 3.9,
            'MINIMUM_WAVELENGTH': 3.8,
            'MAXIMUM_WAVELENGTH': 4.0,
        },
        'supp_index_row': {
            'INSTRUMENT_HOST_ID': 'ESO1M',
            'INSTRUMENT_ID': 'APPH',
            'START_TIME': '1989-07-03T00:00:00.000',
            'STOP_TIME': '1989-07-03T04:00:00.000',
            'PRODUCT_CREATION_TIME': '1998-01-01T00:00:00.000',
            'WAVELENGTH': 3.9,
            'INCIDENCE_ANGLE': 80.0,
            'OCCULTATION_DIRECTION': 'INGRESS',
            'PLANETARY_OCCULTATION_FLAG': 'N',
            'MINIMUM_RING_RADIUS': 74000.0,
            'MAXIMUM_RING_RADIUS': 140000.0,
            'RADIAL_RESOLUTION': 5.0,
        },
        'index_label': {
            'STAR_NAME': '28 SGR',
            'RING_EVENT_START_TIME': '1989-07-03T00:00:00.000',
            'RING_EVENT_STOP_TIME': '1989-07-03T04:00:00.000',
            'MINIMUM_RING_RADIUS': 74000.0,
            'MAXIMUM_RING_RADIUS': 140000.0,
            'RADIAL_RESOLUTION': 5.0,
            'LOWEST_DETECTABLE_OPACITY': 0.01,
            'HIGHEST_DETECTABLE_OPACITY': 3.0,
            'DATA_QUALITY_SCORE': 'GOOD',
            'INCIDENCE_ANGLE': 80.0,
            'EMISSION_ANGLE': 100.0,
            'PHASE_ANGLE': 1.0,
        },
    },
}


def _class_by_name(name: str) -> type[ObsBase]:
    """Return the leaf obs class of that name."""
    for cls in _leaf_classes():
        if cls.__name__ == name:
            return cls
    raise AssertionError(f'no leaf class named {name}')


def _instrument_for(fixture: dict[str, Any]) -> ObsBase:
    """Build an obs instance driven by one mission's metadata fixture."""
    metadata: dict[str, Any] = {
        'phase_name': '',
        'index_row': dict(fixture['index_row']),
        'supp_index_row': dict(fixture.get('supp_index_row', {})),
        'index_label': dict(fixture.get('index_label', {})),
        'supp_index_label': dict(fixture.get('supp_index_label', {})),
        'ring_geo_row': _GeometryRow(),
        'surface_geo_row': _GeometryRow(),
        'sky_geo_row': _GeometryRow(),
        'inventory_list': ['SATURN'],
        'used_surface_geo_targets': ['SATURN'],
        'surface_geo_target_name': 'SATURN',
        'obs_general_row': {'id': 1, 'opus_id': _FakePdsFile.opus_id},
    }
    cls = _class_by_name(fixture['class_name'])
    # The three run arguments an obs class reads, regenerated with
    # `grep -rhoE 'self\._ctx\.args\.[a-z_]+' src/opus_import/obs`. All three are off
    # by default in the real CLI, which is the configuration this drives.
    args = argparse.Namespace(import_fake_images=False,
                              import_ignore_missing_images=False,
                              import_report_inventory_mismatch=False)
    instrument = cls(make_context(args=args), bundle='TEST_BUNDLE', metadata=metadata)
    # There are no holdings here, so the one thing an obs class asks the file system for
    # is answered directly. Everything else it reads comes from the metadata above.
    # Replacing a bound method is the point: there are no holdings here, and this is
    # the one thing an obs class asks the file system for.
    instrument._pdsfile_from_filespec = (  # type: ignore[method-assign]
        lambda filespec: _FakePdsFile())
    return instrument


def _matches(alias: str, value: Any) -> bool:
    """Whether a returned value is one of the things its alias admits."""
    if alias == 'StrField':
        return value is None or isinstance(value, str)
    if alias == 'FloatField':
        return value is None or (isinstance(value, float | int)
                                 and not isinstance(value, bool))
    if alias == 'IntField':
        return value is None or (isinstance(value, int) and not isinstance(value, bool))
    if alias == 'MultFieldRet':
        # An empty list is refused deliberately: a GROUP column produces exactly one
        # value, and `import_observation_table` asserts that in production.
        return _is_mult(value) or (isinstance(value, list) and len(value) > 0
                                   and all(_is_mult(v) for v in value))
    if alias == 'list[MultField]':
        return isinstance(value, list) and all(_is_mult(v) for v in value)
    raise AssertionError(f'unknown alias {alias}')


def _is_mult(value: Any) -> bool:
    """Whether a value is a `opus_import.obs.field_types.MultField`."""
    return isinstance(value, dict) and set(value) == {
        'col_val', 'disp', 'disp_name', 'disp_order', 'grouping', 'group_disp_order',
        'tooltip', 'aliases'}


#: What each mission's fixture drives, measured. Exact rather than a floor, because a
#: floor cannot see one method starting to return None -- which is what a renamed or
#: misspelled index column looks like from here. Regenerate deliberately when a schema
#: or a field method changes, and read a change as something to explain rather than to
#: paper over.
_EXPECTED_RETURNS: dict[str, tuple[int, int]] = {
    'COISS': (316, 271),
    'GOSSI': (300, 253),
    'HSTWFPC2': (308, 237),
    'NHLORRI': (295, 250),
    'VGISS': (303, 251),
    'eso-la_silla.1m04': (285, 235),
}


def _drive(instrument_id: str) -> tuple[list[str], list[str], int, int]:
    """Call every field method the mission's own fixture drives."""
    return _drive_fixture(instrument_id, _MISSION_FIXTURES[instrument_id])


def _drive_fixture(instrument_id: str,
                   fixture: dict[str, Any]) -> tuple[list[str], list[str], int, int]:
    """Call every field method one mission's class resolves.

    Returns:
        What went wrong -- values that do not match their declared type, and methods
        that raised -- followed by how many methods returned at all and how many
        returned something other than an absent value.
    """
    instrument = _instrument_for(fixture)
    assert instrument.instrument_id == instrument_id

    declared = _declared_annotations()
    columns = _schema_columns()
    wrong: list[str] = []
    raised: list[str] = []
    returned = non_null = 0
    for table in _tables_for(instrument):
        for name, column in columns.items():
            if not name.startswith('field_' + table + '_'):
                continue
            if column.get('data_source') != 'COMPUTE':
                continue
            # `_metadata` is `dict | None` on ObsBase; `_instrument_for` always
            # supplies one, which the checker cannot see through the attribute.
            instrument._metadata['table_name'] = table   # type: ignore[index]
            instrument._metadata['field_name'] = (       # type: ignore[index]
                name[len('field_' + table + '_'):])
            try:
                value = getattr(instrument, name)()
            except Exception as exc:
                raised.append(f'{name} raised {type(exc).__name__}: {exc}')
                continue
            returned += 1
            # The alias the method itself declares, not the one the schema implies:
            # layer 1 is what ties those together, and checking the schema's here would
            # make this layer silently depend on that one having run.
            alias = declared[name]
            if not _matches(alias, value):
                wrong.append(f'{name} declares {alias} but returned {value!r}')
            elif value is not None and not (_is_mult(value)
                                            and value['col_val'] is None):
                non_null += 1
    return wrong, raised, returned, non_null


@pytest.mark.parametrize('instrument_id', sorted(_MISSION_FIXTURES))
def test_a_field_method_returns_what_it_declares(instrument_id: str) -> None:
    """Drive one instrument class per mission and check every value against its alias."""
    wrong, _raised, _returned, _non_null = _drive(instrument_id)

    assert wrong == []


@pytest.mark.parametrize('instrument_id', sorted(_MISSION_FIXTURES))
def test_no_field_method_raises_on_a_complete_observation(instrument_id: str) -> None:
    """A fixture carries everything its class reads, so nothing may raise.

    Swallowing exceptions here is what would make this whole layer unfalsifiable: a
    method that starts raising -- or a helper every method depends on, such as
    `opus_import.obs.obs_base.ObsBase._index_col` -- would otherwise just drop out of
    the counts. Each fixture was completed until this reached zero, so a new raise means
    either the code changed or the fixture no longer describes the observation it
    claims to.
    """
    _wrong, raised, _returned, _non_null = _drive(instrument_id)

    assert raised == []


@pytest.mark.parametrize('instrument_id', sorted(_MISSION_FIXTURES))
def test_the_fixture_drives_as_much_of_the_class_as_it_used_to(
        instrument_id: str) -> None:
    """Exactly this many methods return, and exactly this many return a real value.

    The pair is a measurement of behavior, not a budget. A geometry column renamed to
    one that does not exist, an index column misspelled, or a method that starts
    returning None all move the second number, and nothing else in this file would
    notice.
    """
    _wrong, _raised, returned, non_null = _drive(instrument_id)

    assert (returned, non_null) == _EXPECTED_RETURNS[instrument_id]


def test_every_mission_is_represented() -> None:
    """One instrument class per mission, which is what the layer above promises.

    Regenerated from `opus_import.config_data`, so a mission added later fails this
    rather than quietly going unchecked.
    """
    covered = {_class_by_name(f['class_name'])(make_context()).mission_id
               for f in _MISSION_FIXTURES.values()}
    every_mission = set(config_data.MISSION_ID_TO_MISSION_TABLE_SFX) & {
        cls(make_context()).mission_id for cls in _leaf_classes()}

    assert covered == every_mission


def test_the_geometry_row_stands_in_for_a_summary_file() -> None:
    """`_GeometryRow` answers to a real column, to no mask, and to nothing invented."""
    row = _GeometryRow()

    assert 'MINIMUM_RING_RADIUS' in row
    assert row['MINIMUM_RING_RADIUS'] == _GEOMETRY_VALUE
    assert 'MINIMUM_RING_RADIUS_mask' not in row
    assert 'NO_SUCH_GEOMETRY_COLUMN' not in row
    with pytest.raises(KeyError):
        row['NO_SUCH_GEOMETRY_COLUMN']


def test_no_field_method_is_left_unannotated() -> None:
    """Every one of them carries a return annotation, which layer 1 then checks."""
    unannotated = [f'{module}:{line} {cls}.{name}'
                   for module, cls, name, line, annotation in _field_methods()
                   if annotation is None]

    assert unannotated == []


def test_an_integer_column_survives_numpy() -> None:
    """`IntField` means a builtin int, and a PDS index does not hand one out.

    ``pdstable`` parses an integer column with numpy, and `numpy.integer` does not
    subclass `int` -- unlike `numpy.float64` and `numpy.str_`, which do subclass their
    builtins, so only this alias needs the conversion. Without
    `opus_import.obs.field_types.as_int` every `IntField` method reading such a column
    would be declaring something false, and only a runtime check like this one would
    ever say so.
    """
    assert not isinstance(np.int64(7), int), 'numpy started subclassing int'
    assert isinstance(np.float64(7), float)
    assert isinstance(np.str_('x'), str)

    assert isinstance(as_int(np.int64(7)), int)
    assert as_int(np.int64(7)) == 7
    assert as_int(None) is None
    assert as_int('1294561143') == 1294561143


@pytest.mark.parametrize('instrument_id', sorted(_MISSION_FIXTURES))
def test_an_integer_column_is_an_int_even_from_a_numpy_index(
        instrument_id: str) -> None:
    """Drive each mission with numpy-typed index values, as ``pdstable`` produces them.

    The fixtures hold plain Python numbers, which is why the layer above cannot see
    this: every integer column would still look like an `int`. Re-running the same
    sweep with every integer promoted to `numpy.int64` is what makes the conversion
    load-bearing.
    """
    fixture = _MISSION_FIXTURES[instrument_id]
    numpy_fixture = {
        key: ({k: (np.int64(v) if type(v) is int else v) for k, v in value.items()}
              if isinstance(value, dict) else value)
        for key, value in fixture.items()}

    wrong, raised, _returned, _non_null = _drive_fixture(instrument_id, numpy_fixture)

    assert raised == []
    assert wrong == []


def test_the_alias_names_are_the_ones_the_package_defines() -> None:
    """The table names aliases that exist, so a rename cannot leave it checking text."""
    from opus_import.obs import field_types

    for name in ('StrField', 'FloatField', 'IntField', 'MultField', 'MultFieldRet'):
        assert hasattr(field_types, name), name
    assert _alias_for('mult_list', 'MULTIGROUP') == 'list[MultField]'
