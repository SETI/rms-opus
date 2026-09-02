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
unset OPUS_DEPLOY_VENV
unset OPUS_USER
unset OPUS_DB_HOST
unset OPUS_DB_DUMP_DIR
unset OPUS_PEER_DB_HOST
unset OPUS_IMPORT_MAIL_TO
unset OPUS_DEBUG
unset OPUS_ALLOWED_HOSTS
unset OPUS_CACHE_PREFIX
unset OPUS_PUBLIC_URL
unset OPUS_PRODUCT_HTTP_PATH
unset OPUS_VIEWMASTER_URL
unset OPUS_TAR_FILE_URL
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
# deploy fails before it stops Apache rather than half way through. Emptiness is
# refused as well as absence, because nothing downstream objects to an empty value:
# an empty OPUS_SECRET_KEY is a well-formed TOML string and Django starts with no
# secret key.
for _required in \
    OPUS_DIR OPUS_DEPLOY_VENV OPUS_USER OPUS_DB_HOST OPUS_DB_USER OPUS_DB_PASSWORD \
    OPUS_SECRET_KEY PDS3_HOLDINGS_DIR PDS4_HOLDINGS_DIR LAST_BLOG_UPDATE_FILE \
    NOTIFICATION_FILE OPUS_DEBUG OPUS_ALLOWED_HOSTS OPUS_CACHE_PREFIX OPUS_PUBLIC_URL \
    OPUS_PRODUCT_HTTP_PATH OPUS_VIEWMASTER_URL OPUS_TAR_FILE_URL OPUS_DB_DUMP_DIR; do
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
export OPUS_DEPLOY_VENV
export OPUS_USER
export OPUS_DB_HOST
export OPUS_DB_DUMP_DIR
# Optional, and so neither required nor refused above: with no second server there is
# nothing to copy a database to. It is exported all the same, and unset before the
# file is read, so a value left in the caller's environment cannot stand in for one
# the file does not set.
export OPUS_PEER_DB_HOST=${OPUS_PEER_DB_HOST:-}
export OPUS_IMPORT_MAIL_TO=${OPUS_IMPORT_MAIL_TO:-}
export OPUS_DEBUG
export OPUS_ALLOWED_HOSTS
export OPUS_CACHE_PREFIX
export OPUS_PUBLIC_URL
export OPUS_PRODUCT_HTTP_PATH
export OPUS_VIEWMASTER_URL
export OPUS_TAR_FILE_URL
export OPUS_DB_USER
export OPUS_DB_PASSWORD
export OPUS_SECRET_KEY
export PDS3_HOLDINGS_DIR
export PDS4_HOLDINGS_DIR
export LAST_BLOG_UPDATE_FILE
export NOTIFICATION_FILE

# TOML has no truthy strings: `debug = yes` is not a boolean, and the loader refuses
# the file it lands in. Caught here, where the fix is one word in deploy.env, rather
# than at the end of a deploy.
if [[ ${OPUS_DEBUG} != "true" && ${OPUS_DEBUG} != "false" ]]; then
    echo "OPUS_DEBUG in ${SECRETS_DIR}/deploy.env must be 'true' or 'false',"
    echo "not '${OPUS_DEBUG}'."
    exit 1
fi

# Everything a deploy creates belongs to whoever runs it, and the opus.toml it writes
# is mode 0600. Run as anyone but the account the web server's workers run as -- root,
# most easily -- and the deploy succeeds, the switch happens, and the site then cannot
# read its own configuration. Refusing here costs a re-run; finding out afterwards
# costs an outage.
if [[ $(id -un) != "${OPUS_USER}" ]]; then
    echo "These scripts must run as ${OPUS_USER}, the account named by OPUS_USER in"
    echo "${SECRETS_DIR}/deploy.env, and this is $(id -un)."
    echo
    echo "    sudo -u ${OPUS_USER} <the command you ran>"
    echo
    exit 1
fi

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
