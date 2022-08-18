#!/usr/bin/env python

########################################################
### See test_api/TEST_API_README.md for instructions ###
########################################################

import os
import settings
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

    argv = sys.argv
    settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = False
    settings.TEST_GO_LIVE = None

    for cmd_no, command in enumerate(argv):
        if command.startswith('api'):
            if command == 'api-all':
                # Test API only
                argv[cmd_no] = 'test_api/'
            elif command == 'api-result-counts':
                # Test result_counts only (external server)
                argv[cmd_no] = 'test_api.test_result_counts'
            elif command == 'api-internal-db-result-counts':
                # Test result_counts only (internal server)
                argv[cmd_no] = 'test_api.test_result_counts'
                settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = True
            elif command == 'api-livetest-pro':
                # Test against production server opus.pds-rings.seti.org
                # (No VPN required)
                argv[cmd_no] = 'test_api.enable_livetests_pro'
            elif command == 'api-livetest-dev':
                # Test against dev server dev.pds.seti.org
                # (VPN required)
                argv[cmd_no] = 'test_api.enable_livetests_dev'
            elif command == 'api-internal-db':
                # The default - use internal DB
                argv[cmd_no] = 'test_api.enable_livetests_internal'

    from django.core.management import execute_from_command_line

    execute_from_command_line(argv)
    # execute_from_command_line(sys.argv)
