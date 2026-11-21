"""How the search form groups targets by planet, and in what order.

`opus_import.config_targets.target_name_info` says which group each target belongs to;
this says what the group is called and where it sits in the list: a group's
``disp_order`` is its pin, which places it among the field's groups ahead of any group
without one. The entry keyed by None is the group a target with no planet falls into.
"""

from __future__ import annotations

from typing import TypedDict


class PlanetGroup(TypedDict):
    """One planet group of the target field: its name and its pin."""

    label: str
    disp_order: int


PLANET_GROUP_MAPPING: dict[str | None, PlanetGroup] = {
    'MER': {'label': 'Mercury', 'disp_order': 10},
    'VEN': {'label': 'Venus', 'disp_order': 20},
    'EAR': {'label': 'Earth', 'disp_order': 30},
    'MAR': {'label': 'Mars', 'disp_order': 40},
    'JUP': {'label': 'Jupiter', 'disp_order': 50},
    'SAT': {'label': 'Saturn', 'disp_order': 60},
    'URA': {'label': 'Uranus', 'disp_order': 70},
    'NEP': {'label': 'Neptune', 'disp_order': 80},
    'PLU': {'label': 'Pluto', 'disp_order': 90},
    'OTHER': {'label': 'Other', 'disp_order': 100},
    None: {'label': 'NULL', 'disp_order': 110},
}

# For testing purpose, comment out the above PLANET_GROUP_MAPPING
# and uncomment this one.
# PLANET_GROUP_MAPPING = {
#     'MER':   {'label': 'test1/sub1',             'disp_order': 10},
#     'VEN':   {'label': 'test1/sub1/Venus',       'disp_order': 20},
#     'EAR':   {'label': 'test1',                  'disp_order': 30},
#     'MAR':   {'label': 'test1/sub2/sub3/Mars',   'disp_order': 40},
#     'JUP':   {'label': 'test1/sub2/Jupiter',     'disp_order': 50},
#     'SAT':   {'label': 'test2/Saturn',           'disp_order': 60},
#     'URA':   {'label': 'test2/sub1/sub2/Uranus', 'disp_order': 70},
#     'NEP':   {'label': 'test2/sub1',             'disp_order': 80},
#     'PLU':   {'label': 'test3/sub1/sub2/Pluto',  'disp_order': 90},
#     'OTHER': {'label': 'test3/sub1',             'disp_order': 100},
#     None:    {'label': 'NULL',                   'disp_order': 110}
# }
