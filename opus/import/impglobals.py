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

LOGGED_IMPORT_WARNINGS = []
LOGGED_IMPORT_ERRORS = []
IMPORT_HAS_BAD_DATA = False

MAX_TABLE_ID_CACHE = {}

CURRENT_BUNDLE_ID = None
CURRENT_INDEX_ROW_NUMBER = None

TRY_CART_LATER = False
