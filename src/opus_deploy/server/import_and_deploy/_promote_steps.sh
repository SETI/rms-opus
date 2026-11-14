# This file should only be used with "source"
#
# The steps of a promotion that can fail on their own, as functions, so that a test can
# run each one without running _promote.sh.
#
# Defines three functions and runs nothing, so a test can source it.
#
# previous_db_name <deployed opus.toml> <target schema>
#     Prints the schema the served installation's opus.toml names, when that file
#     exists, names a schema, and the schema is not the target. Prints nothing
#     otherwise: on a first deploy, and on a redeploy of the schema being served.
#
# carry_over_sessions <served schema>
#     Replaces the target schema's sessions and carts with the served schema's unexpired
#     sessions that own a cart, and their carts (opus_import
#     --carry-over-sessions-from). It runs while the
#     web service is stopped, before the switch. When it fails it starts the web service
#     again, on the installation that was serving, and returns 1; nothing has switched.
#     It does the same when opus_import --help fails, since that does not show whether
#     the option exists. When the help succeeds and lists no such option, as an older
#     release's does, it warns and returns 0, and the promotion goes on without the
#     carry-over.
#
# warm_search
#     Skipped when OPUS_WARM_SEARCH is exactly "false"; any other value, or none, warms.
#     Asks the site for the landing page and the common searches once (opus_manage
#     warm_search), so the first visitors find them ready. A failure is a warning, never
#     a failed deploy: the site serves, only more slowly at first. Returns 0.
#
# Inputs: OPUS_CONFIG (exported by _opus_setup_environment.sh) naming the staged
# installation's configuration, and that installation's virtualenv active, so that
# opus_import and opus_manage are its own; OPUS_WEB_SERVICE (from _read_deploy_env.sh).
# OPUS_SERVICE_COMMAND, when set, replaces "sudo systemctl" as the command that starts a
# service.

previous_db_name() {
    local deployed_toml=$1
    local target=$2
    local served
    if [[ ! -f ${deployed_toml} ]]; then
        return 0
    fi
    # The rule deploy_new_code_only.sh reads the served schema by.
    served=$(sed -n 's/^schema *= *"\(.*\)"/\1/p' "${deployed_toml}")
    if [[ -n ${served} && ${served} != "${target}" ]]; then
        echo "${served}"
    fi
    return 0
}

carry_over_sessions() {
    local served=$1
    local help
    # A help that cannot be read says nothing about the option, so it fails the promotion.
    if ! help=$(opus_import --help); then
        echo "ERROR: opus_import --help failed, so whether the release being promoted"
        echo "       can carry sessions over is unknown."
        echo "       Nothing has been switched; restarting what was running before."
        ${OPUS_SERVICE_COMMAND:-sudo systemctl} start "${OPUS_WEB_SERVICE}"
        return 1
    fi
    # Going back to a release older than the option promotes it without the carry-over.
    if [[ ${help} != *--carry-over-sessions-from* ]]; then
        echo "WARNING: the release being promoted cannot carry sessions over; the"
        echo "         sessions and carts in ${served} stay there."
        return 0
    fi
    if ! opus_import --carry-over-sessions-from "${served}"; then
        echo "ERROR: could not carry sessions and carts over from ${served}."
        echo "       Nothing has been switched; restarting what was running before."
        ${OPUS_SERVICE_COMMAND:-sudo systemctl} start "${OPUS_WEB_SERVICE}"
        return 1
    fi
    return 0
}

warm_search() {
    if [[ ${OPUS_WARM_SEARCH:-true} == false ]]; then
        echo "Skipping the warm-up: OPUS_WARM_SEARCH is false."
        return 0
    fi
    if ! opus_manage warm_search; then
        echo "WARNING: opus_manage warm_search failed; the site is serving, and the"
        echo "         first visitors' searches fill the cache instead."
    fi
    return 0
}
