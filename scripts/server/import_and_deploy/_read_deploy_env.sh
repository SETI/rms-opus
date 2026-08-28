# This file should only be used via "source"
#
# Read scripts/server/secrets/deploy.env -- the deploy chain's own configuration,
# which is a different thing from the application's opus.toml and is documented as
# such. deploy.env holds the shell-level values these scripts need before any OPUS
# code exists to read anything: where to install, which database credentials to use,
# where the holdings are. opus.toml is what the installed application reads at run
# time, and _write_opus_toml.sh generates it from these values.
#
# Copy scripts/server/deploy.env.template to scripts/server/secrets/deploy.env and
# fill it in. It holds a password and a secret key, so it should be mode 0600.

unset OPUS_DIR
unset OPUS_DB_USER
unset OPUS_DB_PASSWORD
unset OPUS_SECRET_KEY
unset PDS3_HOLDINGS_DIR
unset PDS4_HOLDINGS_DIR
unset LAST_BLOG_UPDATE_FILE
unset NOTIFICATION_FILE

if [[ ! -r ${SECRETS_DIR}/deploy.env ]]; then
    echo "${SECRETS_DIR}/deploy.env is missing or unreadable."
    echo "Copy scripts/server/deploy.env.template to it and fill it in."
    exit 1
fi
source ${SECRETS_DIR}/deploy.env

# Every variable the chain needs, checked here rather than where it is used, so a
# deploy fails before it stops Apache rather than half way through. OPUS_SECRET_KEY
# is in this list because an unset one reaches opus.toml as an empty string, and
# Django then runs with no secret key.
for _required in \
    OPUS_DIR OPUS_DB_USER OPUS_DB_PASSWORD OPUS_SECRET_KEY \
    PDS3_HOLDINGS_DIR PDS4_HOLDINGS_DIR LAST_BLOG_UPDATE_FILE NOTIFICATION_FILE; do
    if [[ ! -v $_required ]]; then
        echo "$_required not defined in ${SECRETS_DIR}/deploy.env"
        exit 1
    fi
    if [[ -z ${!_required} ]]; then
        echo "$_required is empty in ${SECRETS_DIR}/deploy.env"
        exit 1
    fi
    # deploy.env.template ships every value as a quoted <PLACEHOLDER>, so a copy of
    # it that was never filled in sources cleanly and would otherwise reach the
    # generator as a plausible-looking path.
    if [[ ${!_required} == \<*\> ]]; then
        echo "$_required is still the <PLACEHOLDER> from deploy.env.template."
        echo "Fill in ${SECRETS_DIR}/deploy.env."
        exit 1
    fi
done
unset _required

# Exported because _write_opus_toml.sh runs as its own process, which is what makes
# it testable outside a deploy.
export OPUS_DIR
export OPUS_DB_USER
export OPUS_DB_PASSWORD
export OPUS_SECRET_KEY
export PDS3_HOLDINGS_DIR
export PDS4_HOLDINGS_DIR
export LAST_BLOG_UPDATE_FILE
export NOTIFICATION_FILE

if [[ ! -d ${OPUS_DIR} ]]; then
    echo "${OPUS_DIR} does not exist"
    exit 1
fi

if [[ ! -d ${PDS3_HOLDINGS_DIR}/volumes ]]; then
    echo "${PDS3_HOLDINGS_DIR}/volumes does not exist"
    exit 1
fi

if [[ ! -d ${PDS4_HOLDINGS_DIR}/bundles ]]; then
    echo "${PDS4_HOLDINGS_DIR}/bundles does not exist"
    exit 1
fi
