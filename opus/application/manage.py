#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    # pass in livetest to run against actual server
    argv = sys.argv
    for command in argv:
        if command.startswith("api"):
            if command == "api-livetest-pro":
                argv.remove("api-livetest-pro")
                argv.append("test_api/enable_livetests.py")
            elif command == "api-livetest-dev":
                argv.remove("api-livetest-dev")
                argv.append("test_api/enable_livetests_dev.py")
            elif command == "api-internal-db":
                argv.remove("api-internal-db")
                argv.append("test_api/")
            else:
                usage = "To run api test, please choose one of api test commands: "\
                        "api-internal-db, "\
                        "api-livetest-pro, "\
                        "api-livetest-dev"
                print(usage)
                sys.exit()

    from django.core.management import execute_from_command_line

    execute_from_command_line(argv)
    # execute_from_command_line(sys.argv)
