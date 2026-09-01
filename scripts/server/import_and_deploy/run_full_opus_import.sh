#!/bin/bash
#
# Usage: run_full_opus_import.sh [<version_spec>]
#
#   <version_spec>  a PEP 440 specifier appended to the distribution name, for
#                   example '==3.23.0'. Omit it to install the newest release.
#
export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# mktemp rather than a $$-derived name: the PID is predictable and /tmp is
# world-writable, so another local account can pre-create the path -- or a symlink at
# it -- and _full_opus_import_wrapper.sh's redirection would then follow it. mktemp
# creates the file atomically, mode 0600, and fails rather than reusing an existing one.
# The failure is checked because this script has no `set -e` and mktemp is the
# first command here that can fail at all: a $$-derived name could not. Without
# the check an unwritable or full /tmp leaves NOHUP_LOGFILE empty, the wrapper
# dies on `ambiguous redirect` before running anything, and it cannot even mail
# the failure -- while this script goes on to print IMPORT IS RUNNING.
NOHUP_LOGFILE="$(mktemp "${TMPDIR:-/tmp}/opus_import.XXXXXXXX.log")" || {
    echo "Could not create a log file under ${TMPDIR:-/tmp}; import not started." >&2
    exit 1
}
export NOHUP_LOGFILE

# "$@" rather than a bare call: the version specifier has to reach the inner
# script, which otherwise falls back to its own default and installs the newest
# release whatever was named on the command line.
nohup ${IMPORT_SCRIPT_DIR}/_full_opus_import_wrapper.sh "$@" > /dev/null &

echo "*** IMPORT IS RUNNING ***"
echo "Log file: ${NOHUP_LOGFILE}"
