################################################################################
# data_config.py
#
# These configuration parameters are specific to the data sets that are being
# imported. See also mult_config.py.
################################################################################

# param_info form types that invoke mult_ tables
GROUP_FORM_TYPES = ['GROUP', 'TARGETS']

# A list of all tables we populate, in order, for each observation index row.
# If you change something here, be sure to update do_table_names.py as well.
TABLES_TO_POPULATE = ['obs_general',
                      'obs_mission_<MISSION>',
                      'obs_instrument_<INST>',
                      'obs_type_image',
                      'obs_wavelength',
                      'obs_ring_geometry',
                      'obs_surface_geometry',
                      'obs_surface_geometry__<TARGET>']

# These mult tables have an extra column to allow for target_name grouping
MULT_TABLES_WITH_TARGET_GROUPING = ['mult_obs_general_target_name',
                                    'mult_obs_surface_geometry_target_name']

# These instruments have ring geo available (maybe)
INSTRUMENTS_WITH_RING_GEO = ['COCIRS',
                             'COISS',
                             'COUVIS',
                             'COVIMS',
                             'NHLORRI',
                             'VGISS']

# These instruments have surface geo available (maybe)
INSTRUMENTS_WITH_SURFACE_GEO = ['COCIRS',
                                'COISS',
                                'COUVIS',
                                'COVIMS',
                                'NHLORRI',
                                'VGISS']

# Mapping from mission abbreviation (UC) to full mission name (LC)
# These are used for table names
MISSION_ABBREV_TO_MISSION_TABLE_SFX = {
    'CO':  'cassini',
    'GO':  'galileo',
    # 'HST': 'hubble',
    # 'NH':  'new_horizons',
    # 'VG':  'voyager'
}

# Mapping from mission abbreviation (UC) to full mission name (displayable)
MISSION_ABBREV_TO_MISSION_NAME = {
    'CO':  'Cassini',
    'GO':  'Galileo',
    # 'HST': 'Hubble',
    # 'NH':  'New Horizons',
    # 'VG':  'Voyager'
}

# Mapping from instrument host abbreviation to mission abbreviation
INST_HOST_ABBREV_TO_MISSION_ABBREV = {
    'CO':  'CO',
    'GO':  'GO',
    # 'HST': 'HST',
    # 'NH':  'NH',
    # 'VG1': 'VG',
    # 'VG2': 'VG'
}

# Mapping from instrument host abbreviation to instrument host name
INST_HOST_ABBREV_TO_INST_HOST = {
    'CO':  'Cassini',
    'GO':  'Galileo',
    # 'HST': 'Hubble',
    # 'NH':  'New Horizons',
    # 'VG1': 'Voyager 1',
    # 'VG2': 'Voyager 2'
}

# Mapping from instrument abbreviation to mission abbreviation
INSTRUMENT_ABBREV_TO_MISSION_ABBREV = {
    # 'COCIRS':   'CO',
    'COISS':    'CO',
    'COUVIS':   'CO',
    'COVIMS':   'CO',
    'GOSSI':    'GO',
    # 'HSTACS':   'HST',
    # 'HSTWFC3':  'HST',
    # 'HSTWFPC2': 'HST',
    # 'NHLORRI':  'NH',
    # 'NHMVIC':   'NH',
    # 'VGISS':    'VG'
}

# Mapping from instrument abbrev to instrument name
INSTRUMENT_ABBREV_TO_INSTRUMENT_NAME = {
    # 'COCIRS':   'Cassini CIRS',
    'COISS':    'Cassini ISS',
    'COUVIS':   'Cassini UVIS',
    'COVIMS':   'Cassini VIMS',
    'GOSSI':    'Galileo SSI',
    # 'HSTACS':   'Hubble ACS',
    # 'HSTWFC3':  'Hubble WFC3',
    # 'HSTWFPC2': 'Hubble WFPC2',
    # 'NHLORRI':  'New Horizons LORRI',
    # 'NHMVIC':   'New Horizons MVIC',
    # 'VGISS':    'Voyager ISS'
}

# Mapping from VOLUME ID prefix to instrument name
VOLUME_ID_PREFIX_TO_INSTRUMENT_NAME = {
    'COCIRS': 'COCIRS',
    'COISS':  'COISS',
    'COUVIS': 'COUVIS',
    'COVIMS': 'COVIMS',
    'GO':     'GOSSI',
    'HSTIx':  'HSTWFC3',
    'HSTJx':  'HSTACS',
    'HSTOx':  'HSTSTIS',
    'HSTUx':  'HSTWFPC2',
    'NHxxLO': 'NHLORRI',
    'NHxxMV': 'NHMVIC',
    'VGISS':  'VGISS'
}

# Some instruments (I'm looking at you, Cassini) don't use the official IAU
# names for targets, but we want to in OPUS.
TARGET_NAME_MAPPING = {
    # These are found in COISS
    'ERRIAPO':  'ERRIAPUS',
    'HYROKKIN': 'HYRROKKIN',
    'K07S4':    'ANTHE',
    'SKADI':    'SKATHI',
    'SUTTUNG':  'SUTTUNGR',
    'THRYM':    'THRYMR',

    'S7_2004':  'S/2004 S 7',
    'S8_2004':  'S/2004 S 8',
    'S12_2004': 'S/2004 S 12',
    'S13_2004': 'S/2004 S 13',
    'S14_2004': 'S/2004 S 14',
    'S17_2004': 'S/2004 S 17',
    'S18_2004': 'S/2004 S 18',
    'S1_2006':  'S/2006 S 1',
    'S3_2006':  'S/2006 S 3',
    'S2_2007':  'S/2007 S 2',
    'S3_2007':  'S/2007 S 3',

    # These are found in COUVIS
    'ATLAS:':   'ATLAS',
    'AG':       'AEGAEON',
    'DA':       'DAPHNIS',
    'ME':       'METHONE',
    'PL':       'PALLENE',
    'PO':       'POLYDEUCES',
    'IPH':      'INTERSTELLAR MEDIUM', # Interstellar H/He survey

    'CALIB':    'CALIBRATION',
    'UNK':      'UNKNOWN',
}

# Map each possible target name to:
#   1. Planet name it is associated with, or None if not associated with a
#      planet
#   2. Target class
# Note that if you add a new target class here, you also have to update the
# enum field in mult_confic.py for 'mult_obs_general_target_class'
TARGET_NAME_INFO = {
    'NONE':          (None,  'OTHER'),
    'UNKNOWN':       (None,  'OTHER'),
    'CALIBRATION':   (None,  'CALIBRATION'),
    'SKY':           (None,  'SKY'),
    'DARK SKY':      (None,  'SKY'),
    'SUN':           (None,  'SUN'),
    'SOLAR WIND':    (None,  'OTHER'),
    'INTERSTELLAR MEDIUM': (None, 'OTHER'),
    'VENUS':         ('VEN', 'PLANET'),
    'EARTH':         ('EAR', 'PLANET'),
      'MOON':        ('EAR', 'MOON'),
    'JUPITER':       ('JUP', 'PLANET'),
      'ADRASTEA':    ('JUP', 'MOON'),
      'AITNE':       ('JUP', 'MOON'),
      'AMALTHEA':    ('JUP', 'MOON'),
      'ANANKE':      ('JUP', 'MOON'),
      'AOEDE':       ('JUP', 'MOON'),
      'ARCHE':       ('JUP', 'MOON'),
      'AUTONOE':     ('JUP', 'MOON'),
      'CALLIRRHO':   ('JUP', 'MOON'),
      'CALLISTO':    ('JUP', 'MOON'),
      'CARME':       ('JUP', 'MOON'),
      'CARPO':       ('JUP', 'MOON'),
      'CHALDENE':    ('JUP', 'MOON'),
      'CYLLENE':     ('JUP', 'MOON'),
      'ELARA':       ('JUP', 'MOON'),
      'ERINOME':     ('JUP', 'MOON'),
      'EUANTHE':     ('JUP', 'MOON'),
      'EUKELADE':    ('JUP', 'MOON'),
      'EUPORIE':     ('JUP', 'MOON'),
      'EUROPA':      ('JUP', 'MOON'),
      'EURYDOME':    ('JUP', 'MOON'),
      'GANYMEDE':    ('JUP', 'MOON'),
      'HARPALYKE':   ('JUP', 'MOON'),
      'HEGEMONE':    ('JUP', 'MOON'),
      'HELIKE':      ('JUP', 'MOON'),
      'HERMIPPE':    ('JUP', 'MOON'),
      'HERSE':       ('JUP', 'MOON'),
      'HIMALIA':     ('JUP', 'MOON'),
      'IO':          ('JUP', 'MOON'),
      'IOCASTE':     ('JUP', 'MOON'),
      'ISONOE':      ('JUP', 'MOON'),
      'KALE':        ('JUP', 'MOON'),
      'KALLICHOR':   ('JUP', 'MOON'),
      'KALYKE':      ('JUP', 'MOON'),
      'KORE':        ('JUP', 'MOON'),
      'LEDA':        ('JUP', 'MOON'),
      'LYSITHEA':    ('JUP', 'MOON'),
      'MEGACLITE':   ('JUP', 'MOON'),
      'METIS':       ('JUP', 'MOON'),
      'MNEME':       ('JUP', 'MOON'),
      'ORTHOSIE':    ('JUP', 'MOON'),
      'PASIPHAE':    ('JUP', 'MOON'),
      'PASITHEE':    ('JUP', 'MOON'),
      'PRAXIDIKE':   ('JUP', 'MOON'),
      'S/2000 J 11': ('JUP', 'MOON'),
      'S/2003 J 2':  ('JUP', 'MOON'),
      'S/2003 J 3':  ('JUP', 'MOON'),
      'S/2003 J 4':  ('JUP', 'MOON'),
      'S/2003 J 5':  ('JUP', 'MOON'),
      'S/2003 J 9':  ('JUP', 'MOON'),
      'S/2003 J 10': ('JUP', 'MOON'),
      'S/2003 J 12': ('JUP', 'MOON'),
      'S/2003 J 15': ('JUP', 'MOON'),
      'S/2003 J 16': ('JUP', 'MOON'),
      'S/2003 J 18': ('JUP', 'MOON'),
      'S/2003 J 19': ('JUP', 'MOON'),
      'S/2003 J 23': ('JUP', 'MOON'),
      'S/2010 J 1':  ('JUP', 'MOON'),
      'S/2010 J 2':  ('JUP', 'MOON'),
      'S/2011 J 1':  ('JUP', 'MOON'),
      'S/2011 J 2':  ('JUP', 'MOON'),
      'SINOPE':      ('JUP', 'MOON'),
      'SPONDE':      ('JUP', 'MOON'),
      'TAYGETE':     ('JUP', 'MOON'),
      'THEBE':       ('JUP', 'MOON'),
      'THELXINOE':   ('JUP', 'MOON'),
      'THEMISTO':    ('JUP', 'MOON'),
      'THYONE':      ('JUP', 'MOON'),
      'J MINOR SAT': ('JUP', 'MOON'),
      'J RINGS':     ('JUP', 'RING'),
    'SATURN':        ('SAT', 'PLANET'),
      'AEGAEON':     ('SAT', 'MOON'),
      'AEGIR':       ('SAT', 'MOON'),
      'ALBIORIX':    ('SAT', 'MOON'),
      'ANTHE':       ('SAT', 'MOON'),
      'ATLAS':       ('SAT', 'MOON'),
      'BEBHIONN':    ('SAT', 'MOON'),
      'BERGELMIR':   ('SAT', 'MOON'),
      'BESTLA':      ('SAT', 'MOON'),
      'CALYPSO':     ('SAT', 'MOON'),
      'DAPHNIS':     ('SAT', 'MOON'),
      'DIONE':       ('SAT', 'MOON'),
      'ENCELADUS':   ('SAT', 'MOON'),
      'EPIMETHEUS':  ('SAT', 'MOON'),
      'ERRIAPUS':    ('SAT', 'MOON'),
      'FARBAUTI':    ('SAT', 'MOON'),
      'FENRIR':      ('SAT', 'MOON'),
      'FORNJOT':     ('SAT', 'MOON'),
      'GREIP':       ('SAT', 'MOON'),
      'HATI':        ('SAT', 'MOON'),
      'HELENE':      ('SAT', 'MOON'),
      'HYPERION':    ('SAT', 'MOON'),
      'HYRROKKIN':    ('SAT', 'MOON'),
      'IAPETUS':     ('SAT', 'MOON'),
      'IJIRAQ':      ('SAT', 'MOON'),
      'JANUS':       ('SAT', 'MOON'),
      'JARNSAXA':    ('SAT', 'MOON'),
      'K07S4':       ('SAT', 'MOON'),
      'KARI':        ('SAT', 'MOON'),
      'KIVIUQ':      ('SAT', 'MOON'),
      'LOGE':        ('SAT', 'MOON'),
      'METHONE':     ('SAT', 'MOON'),
      'MIMAS':       ('SAT', 'MOON'),
      'MUNDILFARI':  ('SAT', 'MOON'),
      'NARVI':       ('SAT', 'MOON'),
      'PAALIAQ':     ('SAT', 'MOON'),
      'PALLENE':     ('SAT', 'MOON'),
      'PANDORA':     ('SAT', 'MOON'),
      'PAN':         ('SAT', 'MOON'),
      'PHOEBE':      ('SAT', 'MOON'),
      'POLYDEUCES':  ('SAT', 'MOON'),
      'PROMETHEUS':  ('SAT', 'MOON'),
      'RHEA':        ('SAT', 'MOON'),
      'S/2004 S 8':  ('SAT', 'MOON'),
      'S/2004 S 12': ('SAT', 'MOON'),
      'S/2004 S 13': ('SAT', 'MOON'),
      'S/2004 S 14': ('SAT', 'MOON'),
      'S/2004 S 17': ('SAT', 'MOON'),
      'S/2004 S 18': ('SAT', 'MOON'),
      'S/2004 S 7':  ('SAT', 'MOON'),
      'S/2006 S 1':  ('SAT', 'MOON'),
      'S/2006 S 3':  ('SAT', 'MOON'),
      'S/2007 S 2':  ('SAT', 'MOON'),
      'S/2007 S 3':  ('SAT', 'MOON'),
      'SIARNAQ':     ('SAT', 'MOON'),
      'SKATHI':       ('SAT', 'MOON'),
      'SKOLL':       ('SAT', 'MOON'),
      'SURTUR':      ('SAT', 'MOON'),
      'SUTTUNGR':     ('SAT', 'MOON'),
      'TARQEQ':      ('SAT', 'MOON'),
      'TARVOS':      ('SAT', 'MOON'),
      'TELESTO':     ('SAT', 'MOON'),
      'TETHYS':      ('SAT', 'MOON'),
      'THRYMR':       ('SAT', 'MOON'),
      'TITAN':       ('SAT', 'MOON'),
      'YMIR':        ('SAT', 'MOON'),
      'S RINGS':     ('SAT', 'RING'),
    'STAR':          (None,  'STAR'),
      'FOMALHAUT':   (None,  'STAR'),
      'SPICA':       (None,  'STAR'),
    'MASURSKY':      (None,  'ASTEROID'),
}
