#!/usr/bin/env python
import os, sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    # pass in livetest to run against actual server
    argv = sys.argv
    if "live-pro" in argv:
        argv.remove("live-pro")
        argv.append("test_api/enable_livetests.py")
    elif "live-dev" in argv:
        argv.remove("live-dev")
        argv.append("test_api/enable_livetests_dev.py")
    elif "app" in argv:
        argv.remove("app")
        argv.append("test_api/")

    from django.core.management import execute_from_command_line

    execute_from_command_line(argv)
    # execute_from_command_line(sys.argv)
