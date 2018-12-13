#!/usr/bin/env python
import os
import settings
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    # pass in livetest to run against actual server
    argv = sys.argv
    settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = False
    for command in argv:
        if command.startswith("api"):
            if command == "api-livetest-pro":
                argv.remove("api-livetest-pro")
                argv.append("test_api/enable_livetests_pro.py")
            elif command == "api-livetest-dev":
                argv.remove("api-livetest-dev")
                argv.append("test_api/enable_livetests_dev.py")
            elif command == "api-internal-db":
                argv.remove("api-internal-db")
                argv.append("test_api/")
            elif command == "api-internal-db-result-counts":
                argv.remove("api-internal-db-result-counts")
                argv.append("test_api/test_result_counts.py")
                settings.TEST_RESULT_COUNTS_AGAINST_INTERNAL_DB = True
            else:
                usage = "To run api tests, please choose one of these api test commands: "\
                        "\napi-internal-db"\
                        "\napi-internal-db-result-counts"\
                        "\napi-livetest-pro"\
                        "\napi-livetest-dev"
                print(usage)
                sys.exit()

    from django.core.management import execute_from_command_line

    execute_from_command_line(argv)
    # execute_from_command_line(sys.argv)
