# This file should only be used with "source"
#
# One deploy at a time on a server.
#
# Defines one function and runs nothing, so a test can source it.
#
# take_deploy_lock <lock file>
#     Takes an exclusive flock on the file, creating it and its directory, without
#     waiting. The descriptor it locks stays open in the calling shell, so the lock lasts
#     until that shell exits, however it exits. Returns 1, naming the file, when another
#     process holds it.
#
# Both deploy scripts take ${OPUS_DIR}/deploy.lock before they read which schema is being
# served, and hold it through the promotion, which _promote.sh runs in their shell. A
# second deploy started meanwhile stops before it reads or builds anything, so the schema
# a deploy carries sessions and carts over from is still the one being served when it
# promotes, and two deploys never move the deployed symlink in turn.

take_deploy_lock() {
    local lock_file=$1
    mkdir -p -- "$(dirname -- "${lock_file}")"
    exec {OPUS_DEPLOY_LOCK_FD}>>"${lock_file}"
    if ! flock -n "${OPUS_DEPLOY_LOCK_FD}"; then
        echo "ERROR: another deploy holds ${lock_file}; wait for it to finish."
        echo "       The lock goes with the shell that took it, so a deploy that has"
        echo "       exited holds nothing."
        return 1
    fi
    return 0
}
