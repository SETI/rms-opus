################################################################################
# config_targets/planet_group_mapping.py
#
# Group the targets by planet for display, and give each group its position
# in the displayed order.
################################################################################

PLANET_GROUP_MAPPING = {
    'MER':   {'label': 'Mercury', 'disp_order': '010'},
    'VEN':   {'label': 'Venus',   'disp_order': '020'},
    'EAR':   {'label': 'Earth',   'disp_order': '030'},
    'MAR':   {'label': 'Mars',    'disp_order': '040'},
    'JUP':   {'label': 'Jupiter', 'disp_order': '050'},
    'SAT':   {'label': 'Saturn',  'disp_order': '060'},
    'URA':   {'label': 'Uranus',  'disp_order': '070'},
    'NEP':   {'label': 'Neptune', 'disp_order': '080'},
    'PLU':   {'label': 'Pluto',   'disp_order': '090'},
    'OTHER': {'label': 'Other',   'disp_order': '100'},
    None:    {'label': 'NULL',    'disp_order': '110'}
}

# For testing purpose, comment out the above PLANET_GROUP_MAPPING
# and uncomment this one.
# PLANET_GROUP_MAPPING = {
#     'MER':   {'label': 'test1/sub1',             'disp_order': '010'},
#     'VEN':   {'label': 'test1/sub1/Venus',       'disp_order': '020'},
#     'EAR':   {'label': 'test1',                  'disp_order': '030'},
#     'MAR':   {'label': 'test1/sub2/sub3/Mars',   'disp_order': '040'},
#     'JUP':   {'label': 'test1/sub2/Jupiter',     'disp_order': '050'},
#     'SAT':   {'label': 'test2/Saturn',           'disp_order': '060'},
#     'URA':   {'label': 'test2/sub1/sub2/Uranus', 'disp_order': '070'},
#     'NEP':   {'label': 'test2/sub1',             'disp_order': '080'},
#     'PLU':   {'label': 'test3/sub1/sub2/Pluto',  'disp_order': '090'},
#     'OTHER': {'label': 'test3/sub1',             'disp_order': '100'},
#     None:    {'label': 'NULL',                   'disp_order': '110'}
# }
