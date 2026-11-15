# This file should only be used with "source"
#
# The steps of an incremental update, as functions, so that a test can run each one
# without running the update.
#
# An incremental update writes the changed bundles into the served schema as a pending
# import generation, which the site does not show until promote_generation.sh switches it
# in. Each step is its own opus_import process, run against the schema that OPUS_CONFIG
# names, and the first that fails, or that leaves an error in ERRORS.log, stops the update.
#
# Defines these functions and runs nothing, so a test can source it.
#
# print_update_usage
#     Prints the usage line of the update's scripts.
#
# parse_update_arguments [<version_spec>] [--drop <bundle>[,<bundle>...]] [<bundle> ...]
#     Sets OPUS_VERSION_SPEC to the first argument when it begins with a PEP 440
#     operator (= < > ! ~), and empty otherwise; UPDATE_BUNDLES to the bundles to import,
#     the positional arguments split at commas; and UPDATE_DROPS to the bundles to drop,
#     every --drop value split at commas, less any bundle UPDATE_BUNDLES names, since a
#     bundle imported again already loses every row its earlier copy had. --drop may be
#     given more than once; empty names, as from a doubled comma, are skipped. Prints the
#     usage line and returns 1, setting nothing it would otherwise use, when an option is
#     unknown, --drop has no value, a version specifier comes after the first argument,
#     or there is neither a bundle nor a --drop.
#
# update_invocations
#     Prints the arguments of each opus_import invocation of the update, one invocation
#     a line, in order: --begin-generation; --import and the bundles, when there are any;
#     --delete-bundles and the bundles to drop, when there are any; then --finalize,
#     --validate and --write-schema-version. Reads UPDATE_BUNDLES and UPDATE_DROPS.
#
# run_update_invocations <log directory>
#     Runs each invocation update_invocations prints, as its own opus_import process, and
#     after each one checks ERRORS.log in the log directory (check_update_error_log).
#     Returns 0 when every invocation succeeded and logged no error. Otherwise prints
#     ERRORS.log when there is one, and the invocations still to run, and returns 1,
#     having run nothing after the one that failed.
#
# check_update_error_log <log directory>
#     Returns 0 when ERRORS.log in the directory is absent or empty. Otherwise prints it
#     and returns 1. Several import steps report a failure through the log and exit zero,
#     so the log is the gate rather than the status, as in _opus_import_bundles.sh; the
#     update gives each run a log directory of its own, so whatever the file holds was
#     written by this run.
#
# served_schema_name <deployed opus.toml>
#     Prints the schema the served installation's opus.toml names. Prints an error on
#     standard error, so that a command substitution shows it, and returns 1 when the
#     file is missing or names no schema. It reads the file by previous_db_name's rule,
#     so _promote_steps.sh has to be sourced as well.
#
# deployed_release_spec <deployed directory>
#     Prints ==<release> for the rms-opus release the served installation runs, read from
#     its own interpreter, which is what an update installs when given no version
#     specifier. Prints an error on standard error and returns 1 when the release cannot
#     be read, or is a development build (a .dev or local version), which PyPI does not
#     have.

print_update_usage() {
    local usage="Usage: run_incremental_opus_update.sh [<version_spec>]"
    echo "${usage} [--drop <bundle>[,<bundle>...]] [<bundle> ...]"
}

parse_update_arguments() {
    local version_spec=""
    local -a bundles=()
    local -a drops=()
    local -a names
    local name bundle kept
    if [[ ${1:-} == [=\<\>\!~]* ]]; then
        version_spec=$1
        shift
    fi
    while [[ $# -gt 0 ]]; do
        case $1 in
            --drop)
                if [[ $# -lt 2 || -z $2 || $2 == -* ]]; then
                    print_update_usage
                    return 1
                fi
                IFS=, read -ra names <<< "$2"
                for name in "${names[@]}"; do
                    if [[ -n ${name} ]]; then
                        drops+=("${name}")
                    fi
                done
                shift 2
                ;;
            -* | [=\<\>\!~]*)
                print_update_usage
                return 1
                ;;
            *)
                IFS=, read -ra names <<< "$1"
                for name in "${names[@]}"; do
                    if [[ -n ${name} ]]; then
                        bundles+=("${name}")
                    fi
                done
                shift
                ;;
        esac
    done
    if [[ ${#bundles[@]} -eq 0 && ${#drops[@]} -eq 0 ]]; then
        print_update_usage
        return 1
    fi
    OPUS_VERSION_SPEC=${version_spec}
    UPDATE_BUNDLES=("${bundles[@]}")
    UPDATE_DROPS=()
    for name in "${drops[@]}"; do
        kept=true
        for bundle in "${bundles[@]}"; do
            if [[ ${name} == "${bundle}" ]]; then
                kept=false
            fi
        done
        if ${kept}; then
            UPDATE_DROPS+=("${name}")
        fi
    done
    return 0
}

update_invocations() {
    echo "--begin-generation"
    if [[ ${#UPDATE_BUNDLES[@]} -gt 0 ]]; then
        echo "--import ${UPDATE_BUNDLES[*]}"
    fi
    if [[ ${#UPDATE_DROPS[@]} -gt 0 ]]; then
        echo "--delete-bundles ${UPDATE_DROPS[*]}"
    fi
    echo "--finalize"
    echo "--validate"
    echo "--write-schema-version"
}

run_update_invocations() {
    local log_dir=$1
    local -a invocations
    local -a words
    local index remaining
    mapfile -t invocations < <(update_invocations)
    for index in "${!invocations[@]}"; do
        read -ra words <<< "${invocations[index]}"
        echo "** opus_import ${invocations[index]} **"
        echo "Start time:" "$(date)"
        if ! opus_import "${words[@]}"; then
            if [[ -s ${log_dir}/ERRORS.log ]]; then
                cat "${log_dir}/ERRORS.log"
            fi
        elif check_update_error_log "${log_dir}"; then
            echo
            continue
        fi
        echo
        echo "ERROR: opus_import ${invocations[index]} failed or logged errors."
        if [[ ${index} -eq 0 ]]; then
            echo "       No generation was begun, and nothing was changed; the log says why."
            return 1
        fi
        echo "       The pending generation is not served. Either fix the cause and run"
        echo "       what is left, from the installation this update built:"
        for remaining in "${invocations[@]:index}"; do
            echo "           opus_import ${remaining}"
        done
        echo "       or throw the pending generation away and start again:"
        echo "           opus_import --abandon-generation"
        return 1
    done
    return 0
}

check_update_error_log() {
    local errors=$1/ERRORS.log
    if [[ -s ${errors} ]]; then
        echo "** THE UPDATE LOGGED ERRORS **"
        echo
        cat "${errors}"
        return 1
    fi
    return 0
}

served_schema_name() {
    local deployed_toml=$1
    local served
    # previous_db_name with no target prints whatever schema the file names.
    served=$(previous_db_name "${deployed_toml}" "")
    if [[ -z ${served} ]]; then
        echo "ERROR: cannot read the served schema from ${deployed_toml}." >&2
        echo "       Nothing is deployed, or its opus.toml names no schema." >&2
        return 1
    fi
    echo "${served}"
    return 0
}

deployed_release_spec() {
    local deployed=$1
    local release
    release=$("${deployed}/opus_venv/bin/python" -c \
        'import importlib.metadata as m; print(m.version("rms-opus"))' 2> /dev/null) \
        || release=""
    if [[ -z ${release} ]]; then
        echo "ERROR: cannot read the rms-opus release installed in ${deployed}." >&2
        echo "       Give the update the version specifier of the release being served." >&2
        return 1
    fi
    if [[ ${release} == *+* || ${release} == *.dev* ]]; then
        echo "ERROR: ${deployed} runs rms-opus ${release}," >&2
        echo "       a development build PyPI does not have." >&2
        echo "       Give the update the version specifier of a release." >&2
        return 1
    fi
    echo "==${release}"
    return 0
}
