# This file should only be used with "source"
#
# The load itself: replay a dump onto the second server, as load_db.sh's last step.
#
# The dump's CREATE TABLE statements declare the ngram FULLTEXT keys the web
# application's autocomplete reads, so the peer builds those indexes as it loads, under
# this load's own session. Two server settings decide what such an index holds, and the
# dump sets neither:
#
#   ngram_token_size           The length of each run of characters the index holds.
#                              The web application searches for runs of 2, and the
#                              server reads the setting only when it starts, so a peer
#                              with another value is refused before anything is
#                              created.
#   innodb_ft_enable_stopword  The default stopword list holds "a" and "i", and the
#                              ngram parser drops every token that holds a stopword, so
#                              the load turns the list off for its session, ahead of
#                              the dump.
#
# Defines one function and runs nothing, so a test can source it.
#
# load_dump <database> <dump file>
#     Reads the peer's ngram_token_size. When it is not 2, prints why and returns 1,
#     having created nothing. Otherwise creates the database, which fails when it
#     exists, and replays the dump into it on one mysql session whose first statement
#     is "SET SESSION innodb_ft_enable_stopword = OFF;". Returns mysql's status.
#
# Inputs: OPUS_DB_USER, OPUS_DB_PASSWORD and OPUS_PEER_DB_HOST, from deploy.env.

load_dump() {
    local database=$1
    local dump=$2
    local required_token_size=2
    local token_size
    if ! token_size=$(mysql -u"${OPUS_DB_USER}" -p"${OPUS_DB_PASSWORD}" \
            -h "${OPUS_PEER_DB_HOST}" --batch --skip-column-names \
            -e 'SELECT @@GLOBAL.ngram_token_size'); then
        echo "ERROR: cannot read ngram_token_size on ${OPUS_PEER_DB_HOST}."
        return 1
    fi
    if [[ ${token_size} != "${required_token_size}" ]]; then
        echo "ERROR: ${OPUS_PEER_DB_HOST} has ngram_token_size = ${token_size}, and the"
        echo "       database's FULLTEXT indexes need ${required_token_size}. The server"
        echo "       reads ngram_token_size only when it starts: set it to"
        echo "       ${required_token_size} in the server's configuration, restart it,"
        echo "       and load again."
        return 1
    fi
    # The database is created first because a dump holds no CREATE DATABASE, and the
    # load needs something to select. It fails if the database is already there, which
    # is the refusal to want: loading over a database somebody is serving would replace
    # it row by row while they read it.
    echo "CREATE DATABASE ${database};" \
        | mysql -u"${OPUS_DB_USER}" -p"${OPUS_DB_PASSWORD}" -h "${OPUS_PEER_DB_HOST}" \
        || return 1
    { echo 'SET SESSION innodb_ft_enable_stopword = OFF;'; cat "${dump}"; } \
        | mysql -u"${OPUS_DB_USER}" -p"${OPUS_DB_PASSWORD}" -h "${OPUS_PEER_DB_HOST}" \
            "${database}"
}
