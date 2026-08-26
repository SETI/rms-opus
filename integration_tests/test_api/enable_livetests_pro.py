"""Point the API suite at the public production server.

Loaded as a test label by `manage.py api-livetest-pro`; see
`enable_livetests_dev` for the mechanism.
"""

from django.conf import settings

settings.TEST_GO_LIVE = "production"
