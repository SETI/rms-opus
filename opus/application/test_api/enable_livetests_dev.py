# opus/application/test_api/enable_livetests_dev.py 

from test_return_formats import *
from test_vims_image_downlinks import *

testing_target = "dev"
ApiReturnFormatTests.GO_LIVE = True
ApiReturnFormatTests.LIVE_TARGET = testing_target
ApiVimsDownlinksTests.GO_LIVE = True
ApiVimsDownlinksTests.LIVE_TARGET = testing_target
