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
                      'obs_profile',
                      'obs_files',
                      'obs_ring_geometry',
                      'obs_surface_geometry',
                      'obs_surface_geometry_name',
                      'obs_surface_geometry__<TARGET>']

# These mult tables have an extra column to allow for target_name grouping
MULT_TABLES_WITH_TARGET_GROUPING = ['mult_obs_general_target_name',
                                    'mult_obs_surface_geometry_name_target_name']

# Also modify populate_obs_general_preview_images as necessary
VOLSETS_WITH_PREVIEWS = ['COISS_1xxx',
                         'COISS_2xxx',
                         'COCIRS_5xxx',
                         'COCIRS_6xxx',
                         'COUVIS_0xxx',
                         'COUVIS_8xxx',
                         'COVIMS_0xxx',
                         'COVIMS_8xxx',
                         'EBROCC_0xxx',
                         'GO_0xxx',
                         'HSTIx_xxxx',
                         'HSTJx_xxxx',
                         'HSTNx_xxxx',
                         'HSTOx_xxxx',
                         'HSTUx_xxxx',
                         'NHxxLO_xxxx',
                         'NHxxMV_xxxx',
                         'VGISS_5xxx',
                         'VGISS_6xxx',
                         'VGISS_7xxx',
                         'VGISS_8xxx']

# Mapping from mission id (UC) to full mission name (LC)
# These are used for table names
MISSION_ID_TO_MISSION_TABLE_SFX = {
    'CO':  'cassini',
    'GB':  'earth',
    'GO':  'galileo',
    'HST': 'hubble',
    'NH':  'new_horizons',
    'VG':  'voyager'
}

# Mapping from mission id (UC) to full mission name (displayable)
MISSION_ID_TO_MISSION_NAME = {
    'CO':  'Cassini',
    'GB':  'Ground-based',
    'GO':  'Galileo',
    'HST': 'Hubble',
    'NH':  'New Horizons',
    'VG':  'Voyager'
}

# Mapping from instrument host id to mission id
INST_HOST_ID_TO_MISSION_ID = {
    'CO':  'CO',
    'GB':  'GB',
    'GO':  'GO',
    'HST': 'HST',
    'NH':  'NH',
    'VG1': 'VG',
    'VG2': 'VG'
}

# Mapping from instrument host id to instrument host name
INST_HOST_ID_TO_INST_HOST_NAME = {
    'CO':  'Cassini',
    'GB':  'Ground-based',
    'GO':  'Galileo',
    'HST': 'Hubble',
    'NH':  'New Horizons',
    'VG1': 'Voyager 1',
    'VG2': 'Voyager 2'
}

# Mapping from instrument id to mission id
INSTRUMENT_ID_TO_MISSION_ID = {
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
    'VGISS':     'VG',
    'VGPPS':     'VG',
    'VGRSS':     'VG',
    'VGUVS':     'VG',
}

# Mapping from instrument abbrev to instrument name
INSTRUMENT_ID_TO_INSTRUMENT_NAME = {
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
    'VGPPS':       'Voyager PPS',
    'VGRSS':       'Voyager RSS',
    'VGUVS':       'Voyager UVS',
    # Ground-based
    'ESO1MAPPH':   'ESO 1-Meter Aperture Photometer',
    'ESO22MAPPH':  'ESO 2.2-Meter Aperture Photometer',
    'IRTFURAC':    'NASA IRTF URAC',
    'LICK1MCCDC':  'Lick 1-Meter CCD Camera',
    'MCD27MIIRAR': 'McDonald Observatory 2.7-Meter INSB IR Array',
    'PAL200CIRC':  'Palomar Observatory 200-Inch Cassegrain IR Camera'
}

# VGISS: RAW_IMAGE_INDEX
# COCIRS: OBSINDEX
# EBROCC: PROFILE_INDEX
    # 'VG':     {
    #     'VG_2801': 'VGPPS',
    #     'VG_2802': 'VGUVS',
    #     'VG_2803': 'VGRSS',
    #     'VG_2810': 'VGISS',
    # }
# Keywords in supplemental index filenames that indicate they contain surface
# geo info in the absence of an actual surface geo summary file.
# SUPPLEMENTAL_INDEX_FILES_WITH_SURFACE_GEO_INFO = [
#     'CUBE_EQUI'
# ]


# Mapping from VOLUME root to observation type
VOLUME_ID_ROOT_TO_TYPE = {
    'COCIRS_0xxx': 'CUBE',
    'COCIRS_1xxx': 'CUBE',
    'COCIRS_5xxx': 'OBS',
    'COCIRS_6xxx': 'OBS',
    'COISS_1xxx':  'OBS',
    'COISS_2xxx':  'OBS',
    'CORSS_8xxx':  'PROF',
    'COUVIS_0xxx': 'OBS',
    'COUVIS_8xxx': 'PROF',
    'COVIMS_0xxx': 'OBS',
    'COVIMS_8xxx': 'PROF',
    'EBROCC_xxxx': 'PROF',
    'GO_0xxx':     'OBS',
    'HSTIx_xxxx':  'OBS',
    'HSTJx_xxxx':  'OBS',
    'HSTNx_xxxx':  'OBS',
    'HSTOx_xxxx':  'OBS',
    'HSTUx_xxxx':  'OBS',
    'NHxxLO_xxxx': 'OBS',
    'NHxxMV_xxxx': 'OBS',
    'VG_28xx':     'PROF',
    'VGISS_5xxx':  'OBS',
    'VGISS_6xxx':  'OBS',
    'VGISS_7xxx':  'OBS',
    'VGISS_8xxx':  'OBS'
}


# A Dictionary that stores the desired volumes in a volset.
# {volset: pattern of desired volumes}
# If the pattern is not matched, we will skip importing that specific volume.
DESIRED_VOLUMES_IN_VOLSET = {
    # we will ignore volumes smaller than 0402 for COCIRS_0xxx
    'COCIRS_0xxx': r'(COCIRS_040[2-9]|COCIRS_041\d|COCIRS_0[5-9]\d{2})$',
}
