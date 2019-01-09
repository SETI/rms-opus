# opus/application/test_api/enable_livetests_dev.py

import settings

testing_target = "production"
settings.TEST_ApiReturnFormatTests_GO_LIVE = True
settings.TEST_ApiReturnFormatTests_LIVE_TARGET = testing_target
settings.TEST_ApiVimsDownlinksTests_GO_LIVE = True
settings.TEST_ApiVimsDownlinksTests_LIVE_TARGET = testing_target
settings.TEST_ApiMetadataTests_GO_LIVE = True
settings.TEST_ApiMetadataTests_LIVE_TARGET = testing_target
settings.TEST_ApiResultsTests_GO_LIVE = True
settings.TEST_ApiResultsTests_LIVE_TARGET = testing_target
settings.TEST_ApiResultCountsTests_GO_LIVE = True
settings.TEST_ApiResultCountsTests_LIVE_TARGET = testing_target
settings.TEST_ApiSearchTests_GO_LIVE = True
settings.TEST_ApiSearchTests_LIVE_TARGET = testing_target
