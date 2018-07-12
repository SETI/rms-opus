################################################################################
# impglobals.py
#
# Unfortunately, Python doesn't have true globals that can be passed between
# modules. However, we have things, like the logger and currently open database,
# that we want accessible to everyone. Thus we store them in this module where
# everyone can see them.
################################################################################

DATABASE = None
LOGGER = None
ARGUMENTS = None
PYTHON_WARNING_LIST = None

ANNOUNCED_IMPORT_WARNINGS = []
ANNOUNCED_IMPORT_ERRORS = []
IMPORT_HAS_BAD_DATA = False

MAX_TABLE_ID_CACHE = {}
