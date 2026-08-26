"""Point the API suite at the development server.

Loaded as a test label by `manage.py api-livetest-dev`; the assignment below
is the whole point of the module, and `api_test_helper.go_live_target` is what
reads it back.
"""

from django.conf import settings

settings.TEST_GO_LIVE = "dev"
