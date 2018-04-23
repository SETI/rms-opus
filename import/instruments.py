################################################################################
# instruments.py
#
# These are preprocessors and callbacks for PDS label reading to handle the fact
# that so many labels are horribly broken when they are archived.
################################################################################

def _preprocess_uvis_label(lines):
    for i in range(len(lines)):
        line = lines[i]

        if line.startswith('RECORD_TYPE'):
            line = 'RECORD_TYPE = FIXED_LENGTH'
        line = line.replace('^TABLE', '^INDEX_TABLE')
        if line.find('ROW_BYTES') != -1:
            line = line.replace('771', '774') # Required by COUVIS_0001
            line = line.replace('772', '771') # Required by COUVIS_0058
        if line == 'END_OBJECT':
            line = line + ' = INDEX_TABLE'
        lines[i] = line

    return lines

def _preprocess_uvis_table(lines):
    for i in range(len(lines)):
        line = lines[i]

        # This is really awful, but required by COUVIS_0001/INDEX.TAB
        if line.find(b'"USTARE     "') != -1:
            line = line.replace(b'"USTARE     "', b'"USTARE  "')
            line = line[:-5] + b'   ' + line[-5:]

        lines[i] = line

    return lines

def _preprocess_uvis_supp_label(lines):
    for i in range(len(lines)):
        line = lines[i]

        line = line.replace('index_supplement.tab',
                            'supplemental_index.tab')

        lines[i] = line

    return lines

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

def _preprocess_gossi_strip_table(lines):
    for i in range(len(lines)):
        line = lines[i]

        while line[-1] == b'\0':
            line = line[:-1]
        lines[i] = line

    return lines

def _preprocess_gossi_0018_label(lines):
    for i in range(len(lines)):
        line = lines[i]

        if (line.find('FILE_RECORDS') != -1 or
            line.find('ROWS') != -1):
            line = line.replace('481', '567')
        lines[i] = line

    return lines

def _preprocess_gossi_0018_table(lines):
    for i in range(len(lines)):
        line = lines[i]

        while line[-1] == b'\0':
            line = line[:-1]
        lines[i] = line

    return lines

def _preprocess_gossi_0019_label(lines):
    for i in range(len(lines)):
        line = lines[i]

        if (line.find('RECORD_BYTES') != -1 or
            line.find('ROW_BYTES') != -1):
            line = line.replace('743', '744')

        if (line.find('FILE_RECORDS') != -1 or
            line.find('ROWS') != -1):
            line = line.replace('481', '706')
        lines[i] = line

    return lines

def _preprocess_gossi_0020_label(lines):
    for i in range(len(lines)):
        line = lines[i]

        if (line.find('RECORD_BYTES') != -1 or
            line.find('ROW_BYTES') != -1):
            line = line.replace('743', '744')

        if (line.find('FILE_RECORDS') != -1 or
            line.find('ROWS') != -1):
            line = line.replace('481', '704')
        lines[i] = line

    return lines

def _preprocess_gossi_0021_label(lines):
    for i in range(len(lines)):
        line = lines[i]

        if (line.find('RECORD_BYTES') != -1 or
            line.find('ROW_BYTES') != -1):
            line = line.replace('743', '744')

        if (line.find('FILE_RECORDS') != -1 or
            line.find('ROWS') != -1):
            line = line.replace('481', '546')
        lines[i] = line

    return lines

def _preprocess_gossi_0022_label(lines):
    for i in range(len(lines)):
        line = lines[i]

        if (line.find('RECORD_BYTES') != -1 or
            line.find('ROW_BYTES') != -1):
            line = line.replace('743', '744')

        if (line.find('FILE_RECORDS') != -1 or
            line.find('ROWS') != -1):
            line = line.replace('481', '321')
        lines[i] = line

    return lines

def _preprocess_gossi_0023_label(lines):
    for i in range(len(lines)):
        line = lines[i]

        if (line.find('RECORD_BYTES') != -1 or
            line.find('ROW_BYTES') != -1):
            line = line.replace('743', '744')

        if (line.find('FILE_RECORDS') != -1 or
            line.find('ROWS') != -1):
            line = line.replace('481', '678')
        lines[i] = line

    return lines

PDSTABLE_PREPROCESS = [
    ('.*COUVIS_0\d\d\d/INDEX/INDEX.LBL',
        _preprocess_uvis_label, _preprocess_uvis_table),
    ('.*COUVIS_0\d\d\d/.*_SUPPLEMENTAL_INDEX.LBL',
        _preprocess_uvis_supp_label, None),
    ('.*COVIMS_0\d\d\d/INDEX/INDEX.LBL',
        _preprocess_vims_label, None),
    ('.*GO_0017/INDEX/IMGINDEX.LBL',
        None,                         _preprocess_gossi_strip_table),
    ('.*GO_0018/INDEX/IMGINDEX.LBL',
        _preprocess_gossi_0018_label, _preprocess_gossi_strip_table),
    ('.*GO_0019/INDEX/IMGINDEX.LBL',
        _preprocess_gossi_0019_label, _preprocess_gossi_strip_table),
    ('.*GO_0020/INDEX/IMGINDEX.LBL',
        _preprocess_gossi_0020_label, None),
    ('.*GO_0021/INDEX/IMGINDEX.LBL',
        _preprocess_gossi_0021_label, None),
    ('.*GO_0022/INDEX/IMGINDEX.LBL',
        _preprocess_gossi_0022_label, None),
    ('.*GO_0023/INDEX/IMGINDEX.LBL',
        _preprocess_gossi_0023_label, None),
]

PDSTABLE_REPLACEMENTS = [
    ('.*COISS_1\d\d\d/INDEX/INDEX.LBL', {
        'CENTRAL_BODY_DISTANCE': {'NULL': -1e32},
        'DECLINATION': {'NULL': -1e32},
        'EMISSION_ANGLE': {'NULL': -1e32},
        'INCIDENCE_ANGLE': {'NULL': -1e32},
        'LOWER_LEFT_LATITUDE': {'NULL': -1e32},
        'LOWER_LEFT_LONGITUDE': {'NULL': -1e32},
        'LOWER_RIGHT_LATITUDE': {'NULL': -1e32},
        'LOWER_RIGHT_LONGITUDE': {'NULL': -1e32},
        'MAXIMUM_RING_RADIUS': {'NULL': -1e32},
        'MINIMUM_RING_RADIUS': {'NULL': -1e32},
        'NORTH_AZIMUTH_CLOCK_ANGLE': {'NULL': -1e32},
        'PHASE_ANGLE': {'NULL': -1e32},
        'PIXEL_SCALE': {'NULL': -1e32},
        'PLANET_CENTER': {'NULL': -1e32},
        'RIGHT_ASCENSION': {'NULL': -1e32},
        'RING_CENTER_LATITUDE': {'NULL': -1e32},
        'RING_CENTER_LONGITUDE': {'NULL': -1e32},
        'RING_EMISSION_ANGLE': {'NULL': -1e32},
        'RING_INCIDENCE_ANGLE': {'NULL': -1e32},
        'SC_PLANET_POSITION_VECTOR': {'NULL': -1e32},
        'SC_PLANET_VELOCITY_VECTOR': {'NULL': -1e32},
        'SC_SUN_POSITION_VECTOR': {'NULL': -1e32},
        'SC_SUN_VELOCITY_VECTOR': {'NULL': -1e32},
        'SC_TARGET_POSITION_VECTOR': {'NULL': -1e32},
        'SC_TARGET_VELOCITY_VECTOR': {'NULL': -1e32},
        'SUB_SOLAR_LATITUDE': {'NULL': -1e32},
        'SUB_SOLAR_LONGITUDE': {'NULL': -1e32},
        'SUB_SPACECRAFT_LATITUDE': {'NULL': -1e32},
        'SUB_SPACECRAFT_LONGITUDE': {'NULL': -1e32},
        'CENTER_LATITUDE': {'NULL': -1e32},
        'CENTER_LONGITUDE': {'NULL': -1e32},
        'TARGET_DISTANCE': {'NULL': -1e32},
        'TARGET_EASTERNMOST_LONGITUDE': {'NULL': -1e32},
        'TARGET_NORTHERNMOST_LATITUDE': {'NULL': -1e32},
        'TARGET_SOUTHERNMOST_LATITUDE': {'NULL': -1e32},
        'TARGET_WESTERNMOST_LONGITUDE': {'NULL': -1e32},
        'TWIST_ANGLE': {'NULL': -1e32},
        'UPPER_LEFT_LATITUDE': {'NULL': -1e32},
        'UPPER_LEFT_LONGITUDE': {'NULL': -1e32},
        'UPPER_RIGHT_LATITUDE': {'NULL': -1e32},
        'UPPER_RIGHT_LONGITUDE': {'NULL': -1e32},
    }),
    ('.*COUVIS_0\d\d\d/INDEX/INDEX.LBL', {
        'DWELL_TIME': {'NULL': -1e32},
        'INTEGRATION_DURATION': {'NULL': -1e32},
    }),
]
