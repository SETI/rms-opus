#!/usr/bin/env python

########################################################
### See test_api/TEST_API_README.md for instructions ###
########################################################

import cProfile
import io
import os
import pstats
import settings
import sys

from django.core.management import execute_from_command_line


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

    settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = False
    settings.TEST_GO_LIVE = None

    do_profiling = False

    new_argv = []
    for command in sys.argv:
        if command == 'api-all':
            # Test API only
            new_argv.append('test_api')
        elif command == 'api-result-counts':
            # Test result_counts only (external server)
            new_argv.append('test_api.test_result_counts')
        elif command == 'api-internal-db-result-counts':
            # Test result_counts only (internal server)
            new_argv.append('test_api.test_result_counts')
            settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = True
        elif command == 'api-livetest-pro':
            # Test against production server opus.pds-rings.seti.org
            # (No VPN required)
            new_argv.append('test_api.enable_livetests_pro')
        elif command == 'api-livetest-dev':
            # Test against dev server dev.pds.seti.org
            # (VPN required)
            new_argv.append('test_api.enable_livetests_dev')
        elif command == 'api-internal-db':
            # The default - use internal DB
            new_argv.append('test_api.enable_livetests_internal')
        elif command == 'profile':
            # Turn on performance profiling
            do_profiling = True
        else:
            new_argv.append(command)

    if do_profiling:
        pr = cProfile.Profile()
        pr.enable()

    execute_from_command_line(new_argv)

    if do_profiling:
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats(sortby)
        ps.print_stats()
        ps.print_callers()
        with open('profile.txt', 'w') as fp:
            fp.write('Profile results:\n'+s.getvalue())
