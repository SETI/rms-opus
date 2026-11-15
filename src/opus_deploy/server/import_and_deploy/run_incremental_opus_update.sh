#!/bin/bash
#
# Usage: run_incremental_opus_update.sh [<version_spec>]
#            [--drop <bundle>[,<bundle>...]] [<bundle> ...]
#
#   <version_spec>  a PEP 440 specifier appended to the distribution name, for
#                   example '==3.23.0'. Omit it to install the release being served.
#   --drop          bundles to drop from the served database without importing them
#                   again. A bundle named here and as a <bundle> is imported again.
#   <bundle>        bundles to import into the served database: a bundle it holds is
#                   replaced, and one it lacks is added.
#
# At least one bundle or --drop is required. The update is written into the served
# database as a pending generation, which the site does not show until
# promote_generation.sh switches it in.
#
export IMPORT_SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export SCRIPT_DIR=$(dirname "${IMPORT_SCRIPT_DIR}")
export SECRETS_DIR="${SCRIPT_DIR}/secrets"

# The arguments first, so that a mistyped command runs nothing at all.
source "${IMPORT_SCRIPT_DIR}/_incremental_opus_update_steps.sh"
if ! parse_update_arguments "$@"; then
    exit 1
fi

# Read here as well as inside, so that a deploy.env that is missing something, or a
# run started by the wrong account, is refused at once rather than inside a detached
# process whose only trace is a log file nobody is watching yet. It also supplies
# OPUS_IMPORT_MAIL_TO, which the wrapper below needs after the update has ended.
source "${IMPORT_SCRIPT_DIR}/_read_deploy_env.sh"
# mktemp, in TMPDIR or the system's temporary directory, and its failure checked, for the
# reasons run_full_opus_import.sh gives.
NOHUP_LOGFILE="$(mktemp --tmpdir opus_update.XXXXXXXX.log)" || {
    echo "Could not create a log file in the temporary directory; update not started." >&2
    exit 1
}
export NOHUP_LOGFILE

nohup ${IMPORT_SCRIPT_DIR}/_incremental_opus_update_wrapper.sh "$@" > /dev/null &

echo "*** INCREMENTAL UPDATE IS RUNNING ***"
echo "Log file: ${NOHUP_LOGFILE}"
