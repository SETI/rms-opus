# This file should only be used with "source"
#
# Say which release these scripts came out of, and object if it is not the release
# being deployed.
#
# The deploy chain is part of the distribution: `opus_deploy_scripts` writes it out of
# an installed rms-opus, and it changes between releases like anything else. So a copy
# on a server is a copy of one release's chain, and deploying a different release with
# it means running one release's deploy against another release's application --
# which is how a step that a release added, or one it stopped needing, goes missing.
#
# Refreshing the copy is two commands in the environment the chain's own commands come
# from, and it is part of deploying a new release rather than an occasional chore:
#
#     python -m pip install --upgrade "rms-opus==<the release>"
#     opus_deploy_scripts --directory <this directory> --force
#
# `--force` replaces the scripts; it does not touch secrets/, which is not part of
# what ships and so is not part of what is written.
#
# Inputs (exported by the caller): SCRIPT_DIR, and OPUS_VERSION_SPEC when one was
# given on the command line.

if [[ -f ${SCRIPT_DIR}/CHAIN_VERSION ]]; then
    CHAIN_VERSION=$(cat ${SCRIPT_DIR}/CHAIN_VERSION)
    echo "Deploy scripts: rms-opus ${CHAIN_VERSION} (${SCRIPT_DIR})"
else
    CHAIN_VERSION=""
    echo "Deploy scripts: version unrecorded (${SCRIPT_DIR})"
    echo "  These were not written by opus_deploy_scripts, or were written by a"
    echo "  release older than the one that started recording it."
fi

# Only a pinned release can be compared. With no specifier the deploy installs the
# newest release, whose version is not known until pip has run, and warning about
# something unknowable would train an operator to ignore the warning.
if [[ -n ${OPUS_VERSION_SPEC:-} && ${OPUS_VERSION_SPEC} == ==* ]]; then
    DEPLOYING_VERSION=${OPUS_VERSION_SPEC#==}
    if [[ -n ${CHAIN_VERSION} && ${CHAIN_VERSION} != ${DEPLOYING_VERSION} ]]; then
        echo
        echo "*** WARNING: these deploy scripts came from rms-opus ${CHAIN_VERSION},"
        echo "***          and you are deploying ${DEPLOYING_VERSION}."
        echo "***"
        echo "*** Refresh them first:"
        echo "***   python -m pip install --upgrade \"rms-opus==${DEPLOYING_VERSION}\""
        echo "***   opus_deploy_scripts --directory ${SCRIPT_DIR} --force"
        echo
    fi
fi
