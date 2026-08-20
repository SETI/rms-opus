# integration_tests/test_api/enable_livetests_pro.py

from django.conf import settings

settings.TEST_GO_LIVE = "production"
