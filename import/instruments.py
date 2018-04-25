################################################################################
# instruments.py
#
# These are preprocessors and callbacks for PDS label reading to handle the fact
# that so many labels are horribly broken when they are archived.
################################################################################

def _preprocess_vims_label(lines):
    for i in range(len(lines)):
        line = lines[i]

        # In GAIN_MODE_ID and BACKGROUND_SAMPLING_MODE_ID, sometimes N/A is
        # not properly quoted
        if line[:4] in ("GAIN", "BACK"):
            line = line.replace('(N/A',  '("N/A"')
            line = line.replace('N/A)',  '"N/A")')

        # Sometimes a comment begins on one line and and ends on the next
        if line.strip().endswith("*/") and "/*" not in line:
            line = "\n"

        if line.startswith('For full definitions of index fields'):
            line = ''

        line = line.replace('If "OFF"', "If 'OFF'")
        line = line.replace('"N/A" is', "'N/A' is")
        if line.endswith('KM/'):
            line += 'PIXEL"'

        lines[i] = line

    return lines

PDSTABLE_PREPROCESS = [
    # ('.*COUVIS_0\d\d\d/INDEX/INDEX.LBL',
    #     _preprocess_uvis_label, _preprocess_uvis_table),
    # ('.*COUVIS_0\d\d\d/.*_SUPPLEMENTAL_INDEX.LBL',
    #     _preprocess_uvis_supp_label, None),
    ('.*COVIMS_0\d\d\d/INDEX/COVIMS_0\d\d\d_INDEX.LBL',
        _preprocess_vims_label, None),
]

PDSTABLE_REPLACEMENTS = [
    # ('.*COISS_1\d\d\d/INDEX/INDEX.LBL', {
    #     'CENTRAL_BODY_DISTANCE': {'NULL': -1e32},
    #     'DECLINATION': {'NULL': -1e32},
    #     'EMISSION_ANGLE': {'NULL': -1e32},
    #     'INCIDENCE_ANGLE': {'NULL': -1e32},
    #     'LOWER_LEFT_LATITUDE': {'NULL': -1e32},
    #     'LOWER_LEFT_LONGITUDE': {'NULL': -1e32},
    #     'LOWER_RIGHT_LATITUDE': {'NULL': -1e32},
    #     'LOWER_RIGHT_LONGITUDE': {'NULL': -1e32},
    #     'MAXIMUM_RING_RADIUS': {'NULL': -1e32},
    #     'MINIMUM_RING_RADIUS': {'NULL': -1e32},
    #     'NORTH_AZIMUTH_CLOCK_ANGLE': {'NULL': -1e32},
    #     'PHASE_ANGLE': {'NULL': -1e32},
    #     'PIXEL_SCALE': {'NULL': -1e32},
    #     'PLANET_CENTER': {'NULL': -1e32},
    #     'RIGHT_ASCENSION': {'NULL': -1e32},
    #     'RING_CENTER_LATITUDE': {'NULL': -1e32},
    #     'RING_CENTER_LONGITUDE': {'NULL': -1e32},
    #     'RING_EMISSION_ANGLE': {'NULL': -1e32},
    #     'RING_INCIDENCE_ANGLE': {'NULL': -1e32},
    #     'SC_PLANET_POSITION_VECTOR': {'NULL': -1e32},
    #     'SC_PLANET_VELOCITY_VECTOR': {'NULL': -1e32},
    #     'SC_SUN_POSITION_VECTOR': {'NULL': -1e32},
    #     'SC_SUN_VELOCITY_VECTOR': {'NULL': -1e32},
    #     'SC_TARGET_POSITION_VECTOR': {'NULL': -1e32},
    #     'SC_TARGET_VELOCITY_VECTOR': {'NULL': -1e32},
    #     'SUB_SOLAR_LATITUDE': {'NULL': -1e32},
    #     'SUB_SOLAR_LONGITUDE': {'NULL': -1e32},
    #     'SUB_SPACECRAFT_LATITUDE': {'NULL': -1e32},
    #     'SUB_SPACECRAFT_LONGITUDE': {'NULL': -1e32},
    #     'CENTER_LATITUDE': {'NULL': -1e32},
    #     'CENTER_LONGITUDE': {'NULL': -1e32},
    #     'TARGET_DISTANCE': {'NULL': -1e32},
    #     'TARGET_EASTERNMOST_LONGITUDE': {'NULL': -1e32},
    #     'TARGET_NORTHERNMOST_LATITUDE': {'NULL': -1e32},
    #     'TARGET_SOUTHERNMOST_LATITUDE': {'NULL': -1e32},
    #     'TARGET_WESTERNMOST_LONGITUDE': {'NULL': -1e32},
    #     'TWIST_ANGLE': {'NULL': -1e32},
    #     'UPPER_LEFT_LATITUDE': {'NULL': -1e32},
    #     'UPPER_LEFT_LONGITUDE': {'NULL': -1e32},
    #     'UPPER_RIGHT_LATITUDE': {'NULL': -1e32},
    #     'UPPER_RIGHT_LONGITUDE': {'NULL': -1e32},
    # }),
    ('.*COUVIS_0\d\d\d_INDEX.LBL', {
        'DWELL_TIME':           {'    NULL': '    -999'},
        'RIGHT_ASCENSION':           {'    NULL': '    -999'},
        'INTEGRATION_DURATION': {'            NULL': '           -1e32'},
        'TARGET_NAME':          {'N/A             ': 'NONE            '},
    }),
    # ('.*COUVIS_0\d\d\d_SUPPLEMENTAL_INDEX.LBL', {
    #     'DECLINATION':      {'NULL      ': '      -999'},
    #     'RIGHT_ASCENSION':  {'NULL      ': '      -999'},
    # }),
]
