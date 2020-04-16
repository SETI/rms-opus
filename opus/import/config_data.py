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
                      'obs_pds',
                      'obs_mission_<MISSION>',
                      'obs_instrument_<INST>',
                      'obs_type_image',
                      'obs_wavelength',
                      'obs_occultation',
                      'obs_files',
                      'obs_ring_geometry',
                      'obs_surface_geometry',
                      'obs_surface_geometry_name',
                      'obs_surface_geometry__<TARGET>']

# These mult tables have an extra column to allow for target_name grouping
MULT_TABLES_WITH_TARGET_GROUPING = ['mult_obs_general_target_name',
                                   'mult_obs_surface_geometry_name_target_name']

# These instruments have ring geo available (maybe)
# This is only used to give a warning if the ring geo isn't available
INSTRUMENTS_WITH_RING_GEO = ['COISS',
                             'COUVIS',
                             'COVIMS',
                             'NHLORRI',
                             'VGISS']

# These instruments have surface geo available (maybe)
# This is only used to give a warning if the surface geo isn't available
INSTRUMENTS_WITH_SURFACE_GEO = ['COISS',
                                'COUVIS',
                                'COVIMS',
                                'NHLORRI',
                                'VGISS']

# Mapping from mission abbreviation (UC) to full mission name (LC)
# These are used for table names
MISSION_ABBREV_TO_MISSION_TABLE_SFX = {
    'CO':  'cassini',
    'EB':  'earth',
    'GO':  'galileo',
    'HST': 'hubble',
    'NH':  'new_horizons',
    'VG':  'voyager'
}

# Mapping from mission abbreviation (UC) to full mission name (displayable)
MISSION_ABBREV_TO_MISSION_NAME = {
    'CO':  'Cassini',
    'EB':  'Earth-based',
    'GO':  'Galileo',
    'HST': 'Hubble',
    'NH':  'New Horizons',
    'VG':  'Voyager'
}

# Mapping from instrument host abbreviation to mission abbreviation
INST_HOST_ABBREV_TO_MISSION_ABBREV = {
    'CO':  'CO',
    'EB':  'EB',
    'GO':  'GO',
    'HST': 'HST',
    'NH':  'NH',
    'VG1': 'VG',
    'VG2': 'VG'
}

# Mapping from instrument host abbreviation to instrument host name
INST_HOST_ABBREV_TO_INST_HOST = {
    'CO':  'Cassini',
    'EB':  'Earth-based',
    'GO':  'Galileo',
    'HST': 'Hubble',
    'NH':  'New Horizons',
    'VG1': 'Voyager 1',
    'VG2': 'Voyager 2'
}

# Mapping from instrument abbreviation to mission abbreviation
INSTRUMENT_ABBREV_TO_MISSION_ABBREV = {
    'COCIRS':    'CO',
    'COISS':     'CO',
    'CORSS':     'CO',
    'COUVIS':    'CO',
    'COVIMS':    'CO',
    'GOSSI':     'GO',
    'HSTACS':    'HST',
    'HSTNICMOS': 'HST',
    'HSTSTIS':   'HST',
    'HSTWFC3':   'HST',
    'HSTWFPC2':  'HST',
    'NHLORRI':   'NH',
    'NHMVIC':    'NH',
    'VGISS':     'VG'
}

# Mapping from instrument abbrev to instrument name
INSTRUMENT_ABBREV_TO_INSTRUMENT_NAME = {
    'COCIRS':      'Cassini CIRS',
    'COISS':       'Cassini ISS',
    'COUVIS':      'Cassini UVIS',
    'COVIMS':      'Cassini VIMS',
    'GOSSI':       'Galileo SSI',
    'HSTACS':      'Hubble ACS',
    'HSTNICMOS':   'Hubble NICMOS',
    'HSTSTIS':     'Hubble STIS',
    'HSTWFC3':     'Hubble WFC3',
    'HSTWFPC2':    'Hubble WFPC2',
    'NHLORRI':     'New Horizons LORRI',
    'NHMVIC':      'New Horizons MVIC',
    'VGISS':       'Voyager ISS',
    # Earth-based
    'ESO1MAPPH':   'ESO 1-Meter Aperture Photometer',
    'ESO22MAPPH':  'ESO 2.2-Meter Aperture Photometer',
    'IRTFURAC':    'NASA IRTF URAC',
    'LICK1MCCDC':  'Lick 1-Meter CCD Camera',
    'MCD27MIIRAR': 'McDonald Observatory 2.7-Meter INSB IR Array',
    'PAL200CIRC':  'Palomar Observatory 200-Inch Cassegrain IR Camera'
}

# Mapping from VOLUME ID prefix to instrument name
VOLUME_ID_PREFIX_TO_INSTRUMENT_NAME = {
    'COCIRS': 'COCIRS',
    'COISS':  'COISS',
    'CORSS':  'CORSS',
    'COUVIS': 'COUVIS',
    'COVIMS': 'COVIMS',
    'EBROCC': None, # The instrument must be looked up in the label file
    'GO':     'GOSSI',
    'HSTI1':  'HSTWFC3',
    'HSTJ0':  'HSTACS',
    'HSTJ1':  'HSTACS',
    'HSTN0':  'HSTNICMOS',
    'HSTN1':  'HSTNICMOS',
    'HSTO0':  'HSTSTIS',
    'HSTO1':  'HSTSTIS',
    'HSTU0':  'HSTWFPC2',
    'HSTU1':  'HSTWFPC2',
    'NHJULO': 'NHLORRI',
    'NHLALO': 'NHLORRI',
    'NHPCLO': 'NHLORRI',
    'NHPELO': 'NHLORRI',
    'NHJUMV': 'NHMVIC',
    'NHLAMV': 'NHMVIC',
    'NHPCMV': 'NHMVIC',
    'NHPEMV': 'NHMVIC',
    'VGISS':  'VGISS'
}

# Mapping from VOLUME ID prefix to mission abbreviation
VOLUME_ID_PREFIX_TO_MISSION_ABBREV = {
    'COCIRS': 'CO',
    'COISS':  'CO',
    'CORSS':  'CO',
    'COUVIS': 'CO',
    'COVIMS': 'CO',
    'EBROCC': 'EB',
    'GO':     'GO',
    'HSTI1':  'HST',
    'HSTJ0':  'HST',
    'HSTJ1':  'HST',
    'HSTN0':  'HST',
    'HSTN1':  'HST',
    'HSTO0':  'HST',
    'HSTO1':  'HST',
    'HSTU0':  'HST',
    'HSTU1':  'HST',
    'NHJULO': 'NH',
    'NHLALO': 'NH',
    'NHPCLO': 'NH',
    'NHPELO': 'NH',
    'NHJUMV': 'NH',
    'NHLAMV': 'NH',
    'NHPCMV': 'NH',
    'NHPEMV': 'NH',
    'VGISS':  'VG'
}

# Mapping from VOLUME root to observation type
VOLUME_ID_ROOT_TO_TYPE = {
    'COCIRS_5xxx': 'OBS',
    'COCIRS_6xxx': 'OBS',
    'COISS_1xxx':  'OBS',
    'COISS_2xxx':  'OBS',
    'CORSS_8xxx':  'OCC',
    'COUVIS_0xxx': 'OBS',
    'COUVIS_8xxx': 'OCC',
    'COVIMS_0xxx': 'OBS',
    'COVIMS_8xxx': 'OCC',
    'EBROCC_xxxx': 'OCC',
    'GO_0xxx':     'OBS',
    'HSTIx_xxxx':  'OBS',
    'HSTJx_xxxx':  'OBS',
    'HSTNx_xxxx':  'OBS',
    'HSTOx_xxxx':  'OBS',
    'HSTUx_xxxx':  'OBS',
    'NHxxLO_xxxx': 'OBS',
    'NHxxMV_xxxx': 'OBS',
    'VGISS_5xxx':  'OBS',
    'VGISS_6xxx':  'OBS',
    'VGISS_7xxx':  'OBS',
    'VGISS_8xxx':  'OBS'
}

# Some instruments (I'm looking at you, Cassini) don't use the official IAU
# names for targets, but we want to in OPUS.
TARGET_NAME_MAPPING = {
    # These are found in COISS
    'ERRIAPO':          'ERRIAPUS',
    'HYROKKIN':         'HYRROKKIN',
    'K07S4':            'ANTHE',
    'SKADI':            'SKATHI',
    'SUTTUNG':          'SUTTUNGR',
    'THRYM':            'THRYMR',

    'S7_2004':          'S/2004 S 7',
    'S8_2004':          'FORNJOT',
    'S12_2004':         'S/2004 S 12',
    'S13_2004':         'S/2004 S 13',
    'S14_2004':         'HATI',
    'S17_2004':         'S/2004 S 17',
    'S18_2004':         'BESTLA',
    'S1_2006':          'S/2006 S 1',
    'S3_2006':          'S/2006 S 3',
    'S2_2007':          'S/2007 S 2',
    'S3_2007':          'S/2007 S 3',

    # These are found in COUVIS
    'ATLAS:':           'ATLAS',
    'AG':               'AEGAEON',
    'DA':               'DAPHNIS',
    'ME':               'METHONE',
    'PL':               'PALLENE',
    'PO':               'POLYDEUCES',
    'IPH':              'INTERSTELLAR MEDIUM', # Interstellar H/He survey

    # These are found in HST
    '174567-VARDA':     'VARDA',
    '90482ORCUS':       'ORCUS',
    '1999HG12':         '1999 HG12',
    '118378':           '1999 HT11',
    '1999-RT214':       '1999 RT214',
    '80806':            '2000 CM105',
    '60458-2000-CM114': '2000 CM114',
    '2000CQ114':        '2000 CQ114',
    '2000-CQ114':       '2000 CQ114',
    '2000-FC8':         '2000 FC8',
    '2000-OB51':        '2000 OB51',
    '2000-PM30':        '2000 PM30',
    '2000-PN30':        '2000 PN30',
    '2000QN251':        '2000 QN251',
    '2001-FL185':       '2001 FL185',
    '119070':           '2001 KP77',
    '2002VV130':        '2002 VV130',
    '119979':           '2002 WC19',
    '182933':           '2002 GZ31',
    '2002UX25':         '2002 UX25',
    '2003TJ58':         '2003 TJ58',
    '2003QW111':        'MANWE',
    '2003UB313':        'ERIS',
    '2004VE131':        '2004 VE131',
    '2005EF298':        '2005 EF298',
    '2005SE278':        '2005 SE278',
    '2005SF278':        '2005 SF278',
    '2011-JX31':        '2011 JX31',
    '2014MU69':         '2014 MU69',
    '2014PN70':         '2014 PN70',
    'KBO-G1':           '2014 PN70',
    'NECKLACE-NEBULA':  'NECKLACE NEBULA',
    'CHARIKLORING':     'CHARIKLO RING',

    # These are found in NH
    '136472 MAKEMAKE':  'MAKEMAKE',
    '136108 HAUMEA':    'HAUMEA',
    '10199 CHARIKLO':   'CHARIKLO',
    '15810 ARAWN':      'ARAWN',
    '50000 QUAOAR':     'QUAOAR',
    '28978 IXION':      'IXION',
    'ASTEROID 307261':  '2002 MS4',
    '2060 CHIRON':      'CHIRON',
    '132524 APL':       '2002 JF56',

    # Misc
    'S/2000 J 11':      'DIA',

    'CALIB':            'CALIBRATION',
    'N/A':              'NONE',
    'UNK':              'UNKNOWN',
    'UNK SAT':          'UNKNOWN',
    'NON_SCIENC':       'NONE',
    'NON SCIENC':       'NONE',
    'NON SCIENCE':      'NONE',
}

# Map each possible target name to:
#   1. Planet name it is associated with, or None if not associated with a
#      planet
#   2. Target class
# Note that if you add a new target class here, you also have to update the
# enum field and mult_options in obs_general.json
TARGET_NAME_INFO = {
    'NONE':          (None,  'OTHER'),
    'UNKNOWN':       (None,  'OTHER'),
    'OTHER':         (None,  'OTHER'),
    'DARK':          (None,  'CALIBRATION'),
    'CALIBRATION':   (None,  'CALIBRATION'),
    'CAL LAMPS':     (None,  'CALIBRATION', 'Calibration Lamps'),
    'PLAQUE':        (None,  'CALIBRATION'),
    'SKY':           (None,  'SKY'),
    'BLACK SKY':     (None,  'SKY'),
    'DARK SKY':      (None,  'SKY'),
    'SUN':           (None,  'OTHER'),
    'SOLAR WIND':    (None,  'OTHER'),
    'INTERSTELLAR MEDIUM': (None, 'OTHER'),
    'DUST':          (None,  'OTHER'),
    'VENUS':         ('VEN', 'PLANET'),
    'EARTH':         ('EAR', 'PLANET'),
      'MOON':        ('EAR', 'IRR_SAT'),
    'MARS':          ('MAR', 'PLANET'),
    'JUPITER':       ('JUP', 'PLANET'),
      'ADRASTEA':    ('JUP', 'REG_SAT'),
      'AITNE':       ('JUP', 'IRR_SAT'),
      'AMALTHEA':    ('JUP', 'REG_SAT'),
      'ANANKE':      ('JUP', 'IRR_SAT'),
      'AOEDE':       ('JUP', 'IRR_SAT'),
      'ARCHE':       ('JUP', 'IRR_SAT'),
      'AUTONOE':     ('JUP', 'IRR_SAT'),
      'CALLIRRHOE':  ('JUP', 'IRR_SAT'),
      'CALLISTO':    ('JUP', 'REG_SAT'),
      'CARME':       ('JUP', 'IRR_SAT'),
      'CARPO':       ('JUP', 'IRR_SAT'),
      'CHALDENE':    ('JUP', 'IRR_SAT'),
      'CYLLENE':     ('JUP', 'IRR_SAT'),
      'DIA':         ('JUP', 'IRR_SAT'),
      'ELARA':       ('JUP', 'IRR_SAT'),
      'ERINOME':     ('JUP', 'IRR_SAT'),
      'EUANTHE':     ('JUP', 'IRR_SAT'),
      'EUKELADE':    ('JUP', 'IRR_SAT'),
      'EUPORIE':     ('JUP', 'IRR_SAT'),
      'EUROPA':      ('JUP', 'REG_SAT'),
      'EURYDOME':    ('JUP', 'IRR_SAT'),
      'GANYMEDE':    ('JUP', 'REG_SAT'),
      'HARPALYKE':   ('JUP', 'IRR_SAT'),
      'HEGEMONE':    ('JUP', 'IRR_SAT'),
      'HELIKE':      ('JUP', 'IRR_SAT'),
      'HERMIPPE':    ('JUP', 'IRR_SAT'),
      'HERSE':       ('JUP', 'IRR_SAT'),
      'HIMALIA':     ('JUP', 'IRR_SAT'),
      'IO':          ('JUP', 'REG_SAT'),
      'IOCASTE':     ('JUP', 'IRR_SAT'),
      'ISONOE':      ('JUP', 'IRR_SAT'),
      'KALE':        ('JUP', 'IRR_SAT'),
      'KALLICHOR':   ('JUP', 'IRR_SAT'),
      'KALYKE':      ('JUP', 'IRR_SAT'),
      'KORE':        ('JUP', 'IRR_SAT'),
      'LEDA':        ('JUP', 'IRR_SAT'),
      'LYSITHEA':    ('JUP', 'IRR_SAT'),
      'MEGACLITE':   ('JUP', 'IRR_SAT'),
      'METIS':       ('JUP', 'REG_SAT'),
      'MNEME':       ('JUP', 'IRR_SAT'),
      'ORTHOSIE':    ('JUP', 'IRR_SAT'),
      'PASIPHAE':    ('JUP', 'IRR_SAT'),
      'PASITHEE':    ('JUP', 'IRR_SAT'),
      'PRAXIDIKE':   ('JUP', 'IRR_SAT'),
      'S/2003 J 2':  ('JUP', 'IRR_SAT'),
      'S/2003 J 3':  ('JUP', 'IRR_SAT'),
      'S/2003 J 4':  ('JUP', 'IRR_SAT'),
      'S/2003 J 5':  ('JUP', 'IRR_SAT'),
      'S/2003 J 9':  ('JUP', 'IRR_SAT'),
      'S/2003 J 10': ('JUP', 'IRR_SAT'),
      'S/2003 J 12': ('JUP', 'IRR_SAT'),
      'S/2003 J 15': ('JUP', 'IRR_SAT'),
      'S/2003 J 16': ('JUP', 'IRR_SAT'),
      'S/2003 J 18': ('JUP', 'IRR_SAT'),
      'S/2003 J 19': ('JUP', 'IRR_SAT'),
      'S/2003 J 23': ('JUP', 'IRR_SAT'),
      'S/2010 J 1':  ('JUP', 'IRR_SAT'),
      'S/2010 J 2':  ('JUP', 'IRR_SAT'),
      'S/2011 J 1':  ('JUP', 'IRR_SAT'),
      'S/2011 J 2':  ('JUP', 'IRR_SAT'),
      'SINOPE':      ('JUP', 'IRR_SAT'),
      'SPONDE':      ('JUP', 'IRR_SAT'),
      'TAYGETE':     ('JUP', 'IRR_SAT'),
      'THEBE':       ('JUP', 'REG_SAT'),
      'THELXINOE':   ('JUP', 'IRR_SAT'),
      'THEMISTO':    ('JUP', 'IRR_SAT'),
      'THYONE':      ('JUP', 'IRR_SAT'),
      'J MINOR SAT': ('JUP', 'IRR_SAT', 'Jupiter Minor Satellites'),
      'J RINGS':     ('JUP', 'RING',    'Jupiter Rings'),
    'SATURN':        ('SAT', 'PLANET'),
      'AEGAEON':     ('SAT', 'REG_SAT'),
      'AEGIR':       ('SAT', 'IRR_SAT'),
      'ALBIORIX':    ('SAT', 'IRR_SAT'),
      'ANTHE':       ('SAT', 'REG_SAT'),
      'ATLAS':       ('SAT', 'REG_SAT'),
      'BEBHIONN':    ('SAT', 'IRR_SAT'),
      'BERGELMIR':   ('SAT', 'IRR_SAT'),
      'BESTLA':      ('SAT', 'IRR_SAT'),
      'CALYPSO':     ('SAT', 'REG_SAT'),
      'DAPHNIS':     ('SAT', 'REG_SAT'),
      'DIONE':       ('SAT', 'REG_SAT'),
      'ENCELADUS':   ('SAT', 'REG_SAT'),
      'EPIMETHEUS':  ('SAT', 'REG_SAT'),
      'ERRIAPUS':    ('SAT', 'IRR_SAT'),
      'FARBAUTI':    ('SAT', 'IRR_SAT'),
      'FENRIR':      ('SAT', 'IRR_SAT'),
      'FORNJOT':     ('SAT', 'IRR_SAT'),
      'GREIP':       ('SAT', 'IRR_SAT'),
      'HATI':        ('SAT', 'IRR_SAT'),
      'HELENE':      ('SAT', 'REG_SAT'),
      'HYPERION':    ('SAT', 'REG_SAT'),
      'HYRROKKIN':   ('SAT', 'IRR_SAT'),
      'IAPETUS':     ('SAT', 'REG_SAT'),
      'IJIRAQ':      ('SAT', 'IRR_SAT'),
      'JANUS':       ('SAT', 'REG_SAT'),
      'JARNSAXA':    ('SAT', 'IRR_SAT'),
      'K07S4':       ('SAT', 'IRR_SAT'),
      'KARI':        ('SAT', 'IRR_SAT'),
      'KIVIUQ':      ('SAT', 'IRR_SAT'),
      'LOGE':        ('SAT', 'IRR_SAT'),
      'METHONE':     ('SAT', 'REG_SAT'),
      'MIMAS':       ('SAT', 'REG_SAT'),
      'MUNDILFARI':  ('SAT', 'IRR_SAT'),
      'NARVI':       ('SAT', 'IRR_SAT'),
      'PAALIAQ':     ('SAT', 'IRR_SAT'),
      'PALLENE':     ('SAT', 'REG_SAT'),
      'PANDORA':     ('SAT', 'REG_SAT'),
      'PAN':         ('SAT', 'REG_SAT'),
      'PHOEBE':      ('SAT', 'IRR_SAT'),
      'POLYDEUCES':  ('SAT', 'REG_SAT'),
      'PROMETHEUS':  ('SAT', 'REG_SAT'),
      'RHEA':        ('SAT', 'REG_SAT'),
      'S/2004 S 12': ('SAT', 'IRR_SAT'),
      'S/2004 S 13': ('SAT', 'IRR_SAT'),
      'S/2004 S 17': ('SAT', 'IRR_SAT'),
      'S/2004 S 7':  ('SAT', 'IRR_SAT'),
      'S/2006 S 1':  ('SAT', 'IRR_SAT'),
      'S/2006 S 3':  ('SAT', 'IRR_SAT'),
      'S/2007 S 2':  ('SAT', 'IRR_SAT'),
      'S/2007 S 3':  ('SAT', 'IRR_SAT'),
      'SIARNAQ':     ('SAT', 'IRR_SAT'),
      'SKATHI':      ('SAT', 'IRR_SAT'),
      'SKOLL':       ('SAT', 'IRR_SAT'),
      'SURTUR':      ('SAT', 'IRR_SAT'),
      'SUTTUNGR':    ('SAT', 'IRR_SAT'),
      'TARQEQ':      ('SAT', 'IRR_SAT'),
      'TARVOS':      ('SAT', 'IRR_SAT'),
      'TELESTO':     ('SAT', 'REG_SAT'),
      'TETHYS':      ('SAT', 'REG_SAT'),
      'THRYMR':      ('SAT', 'IRR_SAT'),
      'TITAN':       ('SAT', 'REG_SAT'),
      'YMIR':        ('SAT', 'IRR_SAT'),
      'S RINGS':     ('SAT', 'RING',    'Saturn Rings'),
    'URANUS':        ('URA', 'PLANET'),
      'ARIEL':       ('URA', 'REG_SAT'),
      'BELINDA':     ('URA', 'REG_SAT'),
      'BIANCA':      ('URA', 'REG_SAT'),
      'CALIBAN':     ('URA', 'IRR_SAT'),
      'CORDELIA':    ('URA', 'REG_SAT'),
      'CRESSIDA':    ('URA', 'REG_SAT'),
      'CUPID':       ('URA', 'REG_SAT'),
      'DESDEMONA':   ('URA', 'REG_SAT'),
      'FERDINAND':   ('URA', 'IRR_SAT'),
      'FRANCISCO':   ('URA', 'IRR_SAT'),
      'JULIET':      ('URA', 'REG_SAT'),
      'MAB':         ('URA', 'REG_SAT'),
      'MARGARET':    ('URA', 'IRR_SAT'),
      'MIRANDA':     ('URA', 'REG_SAT'),
      'OBERON':      ('URA', 'REG_SAT'),
      'OPHELIA':     ('URA', 'REG_SAT'),
      'PERDITA':     ('URA', 'REG_SAT'),
      'PORTIA':      ('URA', 'REG_SAT'),
      'PROSPERO':    ('URA', 'IRR_SAT'),
      'PUCK':        ('URA', 'REG_SAT'),
      'ROSALIND':    ('URA', 'REG_SAT'),
      'SETEBOS':     ('URA', 'IRR_SAT'),
      'STEPHANO':    ('URA', 'IRR_SAT'),
      'SYCORAX':     ('URA', 'IRR_SAT'),
      'TITANIA':     ('URA', 'REG_SAT'),
      'TRINCULO':    ('URA', 'IRR_SAT'),
      'UMBRIEL':     ('URA', 'REG_SAT'),
      'U RINGS':     ('URA', 'RING',    'Uranus Rings'),
    'NEPTUNE':       ('NEP', 'PLANET'),
      'CHARON':      ('NEP', 'IRR_SAT'),
      'DESPINA':     ('NEP', 'REG_SAT'),
      'GALATEA':     ('NEP', 'REG_SAT'),
      'HALIMEDE':    ('NEP', 'IRR_SAT'),
      'HYDRA':       ('NEP', 'IRR_SAT'),
      'KERBEROS':    ('NEP', 'IRR_SAT'),
      'LAOMEDEIA':   ('NEP', 'IRR_SAT'),
      'LARISSA':     ('NEP', 'REG_SAT'),
      'NAIAD':       ('NEP', 'REG_SAT'),
      'NEREID':      ('NEP', 'IRR_SAT'),
      'NESO':        ('NEP', 'IRR_SAT'),
      'NIX':         ('NEP', 'IRR_SAT'),
      'PLUTO':       ('NEP', 'IRR_SAT'),
      'PROTEUS':     ('NEP', 'REG_SAT'),
      'PSAMATHE':    ('NEP', 'IRR_SAT'),
      'SAO':         ('NEP', 'IRR_SAT'),
      'STYX':        ('NEP', 'IRR_SAT'),
      'THALASSA':    ('NEP', 'REG_SAT'),
      'TRITON':      ('NEP', 'IRR_SAT'),
      'N RINGS':     ('NEP', 'RING',    'Neptune Rings'),
    'PLUTO':         ('PLU', 'PLANET'),
      'CHARON':      ('PLU', 'REG_SAT'),
      'HYDRA':       ('PLU', 'REG_SAT'),
      'KERBEROS':    ('PLU', 'REG_SAT'),
      'NIX':         ('PLU', 'REG_SAT'),
      'STYX':        ('PLU', 'REG_SAT'),

    # Asteroids
    '2002 JF56':     (None,  'OTHER'),
    '2000 CM105':    (None,  'OTHER'), # Minor planet
    'MASURSKY':      (None,  'OTHER'),

    # TNO/KBOs
    'ARAWN':         (None,  'OTHER'),
    'CHARIKLO':      (None,  'OTHER'),
    'CHIRON':        (None,  'OTHER'), # Actually it's a CENTAUR!
    'ERIS':          (None,  'OTHER'),
    'HAUMEA':        (None,  'OTHER'),
    'IXION':         (None,  'OTHER'),
    'MAKEMAKE':      (None,  'OTHER'),
    'MANWE':         (None,  'OTHER'),
    'ORCUS':         (None,  'OTHER'),
    'QUAOAR':        (None,  'OTHER'),
    'SEDNA':         (None,  'OTHER'),
    'VARDA':         (None,  'OTHER'),
    '1999 HG12':     (None,  'OTHER'),
    '1999 HT11':     (None,  'OTHER'),
    '1999 RT214':    (None,  'OTHER'),
    '2000 CQ114':    (None,  'OTHER'),
    '2000 CM114':    (None,  'OTHER'),
    '2000 FC8':      (None,  'OTHER'),
    '2000 OB51':     (None,  'OTHER'),
    '2000 PM30':     (None,  'OTHER'),
    '2000 PN30':     (None,  'OTHER'),
    '2000 QN251':    (None,  'OTHER'),
    '2001 FL185':    (None,  'OTHER'),
    '2001 KP77':     (None,  'OTHER'),
    '2002 GZ31':     (None,  'OTHER'),
    '2002 MS4':      (None,  'OTHER'),
    '2002 UX25':     (None,  'OTHER'),
    '2002 VV130':    (None,  'OTHER'),
    '2002 WC19':     (None,  'OTHER'),
    '2003 TJ58':     (None,  'OTHER'),
    '2004 VE131':    (None,  'OTHER'),
    '2005 EF298':    (None,  'OTHER'),
    '2005 SE278':    (None,  'OTHER'),
    '2005 SF278':    (None,  'OTHER'),
    '2010 JJ124':    (None,  'OTHER'),
    '2011 JX31':     (None,  'OTHER'),
    '2014 MU69':     (None,  'OTHER'),
    '2014 PN70':     (None,  'OTHER'),

    # Other rings
    'CHARIKLO RING': (None,  'RING'),

    # Stars
    'STAR':          (None,  'OTHER'),
      '28 SGR':      (None,  'OTHER'),
      'ARCTURUS':    (None,  'OTHER'),
      'BETA CMA':    (None,  'OTHER'),
      'FOMALHAUT':   (None,  'OTHER'),
      'HD 37962':    (None,  'OTHER'),
      'HD 205905':   (None,  'OTHER'),
      'NGC 3532':    (None,  'OTHER'),
      'ORION':       (None,  'OTHER'),
      'PLEIADES':    (None,  'OTHER'),
      'SCORPIUS':    (None,  'OTHER'),
      'SIGMA SGR':   (None,  'OTHER'),
      'SPICA':       (None,  'OTHER'),
      'TAURUS':      (None,  'OTHER'),
      'THETA CAR':   (None,  'OTHER'),
      'VEGA':        (None,  'OTHER'),

    # Comets
    'SHOEMAKER LEVY 9': (None,  'OTHER'),

    # Nebulae
    'NECKLACE NEBULA': (None,  'OTHER'),

    # Misc
    'FLATFIELD':     (None,  'OTHER'),
    'ACQ-ECLPSE':    (None,  'OTHER'),
    'SYSTEM':        (None,  'OTHER'),
    'M7':            (None,  'OTHER'), # Open Cluster
}

# Map each star name to its RA and DEC
STAR_RA_DEC = {
    '28 SGR': (18/24.+46/60.+20.61/3600., -(22+23/60.+31.83/3600.))
}
