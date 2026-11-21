# This file should only be used with "source"
#
# What happens to a database a run script has finished: the end of both
# _run_full_opus_import.sh and _run_incremental_opus_update.sh, which source this file and
# call copy_database_to_peer, so that the two cannot copy a database differently.
#
# Defines two functions and runs nothing, so a test can source it.
#
# new_schema_name <moment and process>
#     Prints the name a schema new to a server takes: opus3_ followed by the argument,
#     which the run scripts make from the time they started and their process id.
#
# copy_database_to_peer <source schema> <target schema>
#     With OPUS_DB_DUMP_DIR empty, does nothing. With a directory there, dumps the source
#     schema into it under the target schema's name (dump_db.sh), so an update's dump of
#     the served schema never replaces a dump an operator took of it under its own name;
#     with OPUS_PEER_DB_HOST naming a host as well, then loads that dump onto the host as
#     the target schema (load_db.sh), which must not exist there. Returns 1 when either
#     script fails, 0 otherwise.
#
# Inputs: DATABASE_SCRIPT_DIR, the chain's database/ directory; OPUS_DB_DUMP_DIR and
# OPUS_PEER_DB_HOST, from _read_deploy_env.sh.

new_schema_name() {
    echo "opus3_$1"
}

copy_database_to_peer() {
    local source_schema=$1
    local target_schema=$2
    # What happens to the finished database, which is whatever deploy.env asked for. With
    # OPUS_DB_DUMP_DIR empty the run is done when the database is built -- a dump of the
    # full holdings is tens of gigabytes and hours of writing, so it happens because a
    # server asked for it. With a directory but no peer, the dump is written and stays
    # there; with both, it is written and loaded onto the second server. A peer with no
    # directory cannot happen: _read_deploy_env.sh refuses that combination before any of
    # this runs.
    if [[ -n ${OPUS_DB_DUMP_DIR} ]]; then
        echo "================================"
        echo "=== DUMP DATABASE TO ARCHIVE ==="
        echo "================================"
        echo
        echo "Start time:" `date`
        echo
        "${DATABASE_SCRIPT_DIR}/dump_db.sh" "${source_schema}" "${target_schema}" || return 1
        echo
        echo

        if [[ -n ${OPUS_PEER_DB_HOST} ]]; then
            echo "==========================================="
            echo "=== LOAD DATABASE ON THE SECOND SERVER  ==="
            echo "==========================================="
            echo
            echo "Start time:" `date`
            echo
            "${DATABASE_SCRIPT_DIR}/load_db.sh" "${target_schema}" || return 1
            echo
            echo
        fi
    fi
    return 0
}
