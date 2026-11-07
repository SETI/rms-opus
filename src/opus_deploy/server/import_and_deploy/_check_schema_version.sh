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
#     Reads the release's version through the staged installation's python, and the
#     served database's row through the same python, using the opus.toml that
#     OPUS_CONFIG names. Returns 0 when they agree and the row is "ready". Otherwise
#     prints what is wrong and the remedy, and returns 1.
#
# Inputs: OPUS_CONFIG (exported by _opus_setup_environment.sh), and the staged
# installation's virtualenv active, so that python is that installation's.

check_schema_version() {
    local release served version state
    if ! release=$(python -c 'from opus_import.schema_version import SCHEMA_VERSION; print(SCHEMA_VERSION)'); then
        echo "ERROR: cannot read the release's schema version from the staged installation."
        return 1
    fi
    if ! served=$(python -c 'from opus_import.schema_version import served_row; print(served_row())'); then
        echo "ERROR: cannot read the schema_version row of the database ${OPUS_CONFIG} names."
        return 1
    fi
    echo "Schema version: release ${release}, database ${served}"
    read -r version state <<< "${served}"
    if [[ ${served} == absent ]]; then
        echo "ERROR: the database has no schema_version row, so no release finished it."
        echo "       Re-import it under this release (run_full_opus_import.sh); if it was"
        echo "       imported by this release, finish it with"
        echo "       'opus_import --write-schema-version'."
        return 1
    fi
    if [[ ${state} == rows ]]; then
        echo "ERROR: the database's schema_version table holds ${version} rows, not one."
        echo "       Re-import it under this release (run_full_opus_import.sh)."
        return 1
    fi
    if [[ ${version} != "${release}" ]]; then
        echo "ERROR: the database is schema version ${version}, and this release is"
        echo "       version ${release}. Re-import it under this release"
        echo "       (run_full_opus_import.sh) and deploy that database"
        echo "       (deploy_new_code_and_database.sh)."
        return 1
    fi
    if [[ ${state} != ready ]]; then
        echo "ERROR: the database's state is '${state}', not 'ready': an import or an"
        echo "       append to it has not finished. Finish it, ending with"
        echo "       'opus_import --write-schema-version'."
        return 1
    fi
    return 0
}
