################################################################################
# instruments.py
#
# These are preprocessors and callbacks for PDS label reading to handle the fact
# that so many labels are horribly broken when they are archived.
################################################################################

PDSTABLE_PREPROCESS = [
    # ('.*COUVIS_0\d\d\d/INDEX/INDEX.LBL',
    #     _preprocess_uvis_label, _preprocess_uvis_table),
    # ('.*COUVIS_0\d\d\d/.*_SUPPLEMENTAL_INDEX.LBL',
    #     _preprocess_uvis_supp_label, None),
    # ('.*COVIMS_0\d\d\d/INDEX/COVIMS_0\d\d\d_INDEX.LBL',
    #     _preprocess_vims_label, None),
]

PDSTABLE_REPLACEMENTS = [
    # ('.*COUVIS_0\d\d\d_INDEX.LBL', {
    #     'DWELL_TIME':           {'    NULL': '    -999'},
    #     'INTEGRATION_DURATION': {'            NULL': '           -1e32'},
    #     'TARGET_NAME':          {'N/A             ': 'NONE            '},
    # }),
]
