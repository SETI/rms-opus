# This file should only be used with "source"
#
# What a deploy installs, from the <version_spec> its command line names.
#
# A version spec is one of:
#
#   a PEP 440 specifier, appended to the distribution name and installed from PyPI:
#   "==<release>" for a release, ">=<release>" and the like for the newest that matches;
#
#   "@" and a git ref -- a branch, a tag or a commit -- installed from the rms-opus
#   repository (OPUS_GIT_REPOSITORY): "@<branch, tag or commit>". This is how a branch
#   with no release is deployed. pip builds it from a clone, so the server needs git and
#   access to the repository, and the installation reports a development version;
#
#   empty, for the newest release on PyPI.
#
# Defines these functions and the repository, and runs nothing else, so a test can
# source it.
#
# is_version_spec <argument>
#     Returns 0 when the argument is a version spec other than empty: it begins with a
#     PEP 440 operator (= < > ! ~), or it is "@" followed by a git ref made of letters,
#     digits, ".", "_", "/" and "-" that neither begins with "-" nor holds "..".
#     Returns 1 otherwise.
#
# check_version_spec <script name> [<version spec>]
#     Returns 0 when the spec is empty or a version spec. Otherwise prints an error
#     naming the script and both forms, and returns 1, so a mistyped spec is refused
#     before anything runs rather than by pip once the installation is half built.
#
# opus_requirement [<version spec>]
#     Prints the requirement pip installs for the spec: "rms-opus<specifier>" for a
#     PEP 440 specifier or none, and "rms-opus @ git+<repository>@<ref>" for a git ref.

#: The repository a git ref is installed from.
OPUS_GIT_REPOSITORY=https://github.com/SETI/rms-opus.git

is_version_spec() {
    local argument=$1
    if [[ ${argument} == [=\<\>\!~]* ]]; then
        return 0
    fi
    if [[ ${argument} =~ ^@[A-Za-z0-9._/][A-Za-z0-9._/-]*$ && ${argument} != *..* ]]; then
        return 0
    fi
    return 1
}

check_version_spec() {
    local script=$1
    local spec=${2:-}
    if [[ -z ${spec} ]] || is_version_spec "${spec}"; then
        return 0
    fi
    echo "ERROR: ${script}: '${spec}' is not a version spec. Give a PEP 440 specifier,"
    echo "       such as '==3.25.0', or '@' and a git branch, tag or commit, such as"
    echo "       '@main'."
    return 1
}

opus_requirement() {
    local spec=${1:-}
    if [[ ${spec} == @* ]]; then
        echo "rms-opus @ git+${OPUS_GIT_REPOSITORY}${spec}"
    else
        echo "rms-opus${spec}"
    fi
}
