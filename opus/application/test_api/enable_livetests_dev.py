# opus/application/test_api/enable_livetests_dev.py

from test_return_formats import ApiReturnFormatTests
from test_vims_image_downlinks import ApiVimsDownlinksTests
from test_metadata_api import ApiMetadataTests
from test_result_counts import APIResultCountsTests
from test_results_api import ApiResultsTests

testing_target = "dev"
ApiReturnFormatTests.GO_LIVE = True
ApiReturnFormatTests.LIVE_TARGET = testing_target
ApiVimsDownlinksTests.GO_LIVE = True
ApiVimsDownlinksTests.LIVE_TARGET = testing_target
ApiMetadataTests.GO_LIVE = True
ApiMetadataTests.LIVE_TARGET = testing_target
ApiResultsTests.GO_LIVE = True
ApiResultsTests.LIVE_TARGET = testing_target
APIResultCountsTests.GO_LIVE = True
APIResultCountsTests.LIVE_TARGET = testing_target
