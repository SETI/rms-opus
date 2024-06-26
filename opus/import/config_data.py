################################################################################
# config_data.py
#
# Define general constants and mappings useful throughout the import process.
################################################################################


# param_info form types that invoke mult_ tables
GROUP_FORM_TYPES = ['GROUP', 'MULTIGROUP']

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

# Mapping from instrument id to instrument name.
# This only includes the keys from the INSTRUMENT_ID_TO_MISSION_ID table;
# these are the instruments that have their own obs_ table.
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
}
