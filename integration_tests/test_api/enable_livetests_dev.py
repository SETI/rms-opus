# integration_tests/test_api/enable_livetests_dev.py

from django.conf import settings

settings.TEST_GO_LIVE = "dev"
