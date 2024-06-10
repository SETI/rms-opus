# This file should only be used via "source"
unset OPUS_DIR
unset OPUS_DB_USER
unset OPUS_DB_PASSWORD
unset PDS3_HOLDINGS_DIR
unset PDS4_HOLDINGS_DIR
unset LAST_BLOG_UPDATE_FILE
unset NOTIFICATION_FILE
source ${SECRETS_DIR}/opus_secrets

if [[ ! -v OPUS_DIR ]]; then
    echo "OPUS_DIR not defined in opus_secrets"
    exit -1
fi

if [[ ! -v OPUS_DB_USER ]]; then
    echo "OPUS_DB_USER not defined in opus_secrets"
    exit -1
fi

if [[ ! -v OPUS_DB_PASSWORD ]]; then
    echo "OPUS_DB_PASSWORD not defined in opus_secrets"
    exit -1
fi

if [[ ! -v PDS3_HOLDINGS_DIR ]]; then
    echo "PDS3_HOLDINGS_DIR not defined in opus_secrets"
    exit -1
fi

if [[ ! -v PDS4_HOLDINGS_DIR ]]; then
    echo "PDS4_HOLDINGS_DIR not defined in opus_secrets"
    exit -1
fi

if [[ ! -d ${OPUS_DIR} ]]; then
    echo "${OPUS_DIR} does not exist"
    exit -1
fi

if [[ ! -d ${PDS3_HOLDINGS_DIR}/volumes ]]; then
    echo "${PDS3_HOLDINGS_DIR}/volumes does not exist"
    exit -1
fi

if [[ ! -d ${PDS4_HOLDINGS_DIR}/bundles ]]; then
    echo "${PDS4_HOLDINGS_DIR}/bundles does not exist"
    exit -1
fi

if [[ ! -v LAST_BLOG_UPDATE_FILE ]]; then
    echo "LAST_BLOG_UPDATE_FILE not defined in opus_secrets"
    exit -1
fi

if [[ ! -v NOTIFICATION_FILE ]]; then
    echo "NOTIFICATION_FILE not defined in opus_secrets"
    exit -1
fi
