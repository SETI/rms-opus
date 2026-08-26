"""Point the API suite at the locally imported database, which is the default.

Loaded as a test label by `manage.py api-internal-db`. It deliberately does
nothing: `manage.py` has already set the go-live target to None, and this
module exists so that verb has a label to name.
"""

