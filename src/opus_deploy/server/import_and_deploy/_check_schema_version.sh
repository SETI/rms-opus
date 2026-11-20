# This file should only be used with "source"
#
# Refuse to deploy a release onto a database it cannot serve.
#
# Every OPUS table is created by the import from the table schemas that ship with the
# release, and a finished database records which generation of them imported it: a
# one-row schema_version table holding a version and a state. The web application
# serves a database only when that row holds the release's own version
# (opus_import.schema_version.SCHEMA_VERSION) in the "ready" state, and answers every
# request 503 otherwise. Checking the same thing here, before anything is installed
# over or written to, turns that 503 into a deploy that stops and says why.
#
# Defines one function and runs nothing, so a test can source it.
#
# check_schema_version
#     Asks the staged installation's opus_import whether it would serve the database
#     that OPUS_CONFIG names (opus_import --check serve, the web application's own
#     rule), which logs what is wrong when it would not. Returns 0 when it would.
#     Otherwise prints the remedy, and returns 1; likewise, saying so, when the database
#     cannot be read.
#
# Inputs: OPUS_CONFIG (exported by _opus_setup_environment.sh), and the staged
# installation's virtualenv active, so that opus_import is that installation's.

check_schema_version() {
    # The status opus_import --check exits with when the action would be refused
    # (opus_import.steps.do_generation.GENERATION_REFUSED_EXIT_STATUS).
    local refused=3
    local status=0
    opus_import --check serve || status=$?
    if [[ ${status} -ne 0 && ${status} -ne ${refused} ]]; then
        echo "ERROR: cannot read the schema_version row of the database ${OPUS_CONFIG} names."
        return 1
    fi
    if [[ ${status} -eq ${refused} ]]; then
        echo "ERROR: this release would not serve the database; the check above says why."
        echo "       Re-import it under this release (run_full_opus_import.sh) and deploy"
        echo "       that database (deploy_new_code_and_database.sh). A database this"
        echo "       release imported and did not finish needs its finishing steps instead:"
        echo "       opus_import --finalize, --import-dictionary and --validate, then"
        echo "       opus_import --write-schema-version."
        return 1
    fi
    echo "Schema version: the database is this release's, and ready."
    return 0
}
