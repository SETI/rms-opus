#!/usr/bin/env python
import os
import settings
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    # pass in livetest to run against actual server
    argv = sys.argv
    settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = False
    settings.TEST_GO_LIVE = None

    for cmd_no, command in enumerate(argv):
        if command == 'all':
            argv[cmd_no] = "test_api/"
        if command.startswith("api"):
            if command == "api-livetest-pro":
                argv[cmd_no] = "test_api/enable_livetests_pro.py"
            elif command == "api-livetest-dev":
                argv[cmd_no] = "test_api/enable_livetests_dev.py"
            elif command == "api-internal-db":
                argv[cmd_no] = "test_api/"
            elif command == "api-internal-db-result-counts":
                argv[cmd_no] = "test_api/test_result_counts.py"
                settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = True
            else:
                usage = "To run api tests, please choose one of these api test commands: "\
                        "\napi-internal-db"\
                        "\napi-internal-db-result-counts"\
                        "\napi-livetest-pro"\
                        "\napi-livetest-dev"\
                        "\nSpecify all to test all server tests"
                print(usage)
                sys.exit()

    from django.core.management import execute_from_command_line

    execute_from_command_line(argv)
    # execute_from_command_line(sys.argv)
