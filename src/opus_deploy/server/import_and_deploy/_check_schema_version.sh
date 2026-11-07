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
#     Asks the staged installation's python what would keep the database that
#     OPUS_CONFIG names from being served (served_schema_version_problem, the web
#     application's own rule). Returns 0 when nothing would. Otherwise prints what is
#     wrong and the remedy, and returns 1; likewise when the database cannot be read.
#
# Inputs: OPUS_CONFIG (exported by _opus_setup_environment.sh), and the staged
# installation's virtualenv active, so that python is that installation's.

check_schema_version() {
    local found
    if ! found=$(python -c 'from opus_import.schema_version import served_schema_version_problem as p; print(p() or "")'); then
        echo "ERROR: cannot read the schema_version row of the database ${OPUS_CONFIG} names."
        return 1
    fi
    if [[ -n ${found} ]]; then
        echo "ERROR: this release would not serve the database: ${found}."
        echo "       Re-import it under this release (run_full_opus_import.sh) and deploy"
        echo "       that database (deploy_new_code_and_database.sh), unless this release"
        echo "       imported it and only the last step is missing."
        return 1
    fi
    echo "Schema version: the database is this release's, and ready."
    return 0
}
