# This file should only be used with "source"
#
# Make a staged installation the one being served.
#
# A deploy is two halves, and this is the second. The first half builds a complete
# installation under ${OPUS_DIR}/staged -- its own virtualenv, its own rms-opus
# release, its own opus.toml naming its own database -- and touches nothing that is
# running. This half switches to it. A failure anywhere in the first half therefore
# leaves the site serving exactly what it was serving before.
#
# The switch has to move the code and the database together. A release that changes
# the table schemas cannot read the database the previous release imported, and the
# previous release cannot read the new one, so a deploy that changed the code in
# place -- or changed the configuration in place -- would serve one against the
# other for as long as it took to finish. Here they are one directory, and the
# switch is one symlink.
#
# Inputs (exported by the caller): OPUS_DIR, INSTALL_DIR naming the staged
# installation to promote, and the two service names _read_deploy_env.sh supplies,
# OPUS_WEB_SERVICE and OPUS_CACHE_SERVICE.

if [[ ! -v OPUS_DIR ]]; then
    echo "INTERNAL ERROR: OPUS_DIR undefined"
    exit 1
fi
if [[ ! -v INSTALL_DIR ]]; then
    echo "INTERNAL ERROR: INSTALL_DIR undefined"
    exit 1
fi
if [[ ! -f "${INSTALL_DIR}/opus.toml" || ! -e "${INSTALL_DIR}/wsgi.py" ]]; then
    echo "ERROR: ${INSTALL_DIR} is not a complete installation."
    echo "       Nothing has been switched; the running installation is untouched."
    exit 1
fi

echo "Promoting ${INSTALL_DIR}"

# The workers are stopped for the switch rather than across the whole deploy:
# everything slow -- the virtualenv, the pip install, the migration, collectstatic --
# has already happened by the time this runs. They are stopped rather than restarted
# afterwards because a worker that read the old installation's configuration would go
# on answering from the old database until it was replaced.
sudo systemctl stop "${OPUS_WEB_SERVICE}"

# `ln -sfn` would do this in two steps, unlinking the old symlink before creating
# the new one, and a deploy interrupted between them leaves no ${OPUS_DIR}/deployed
# at all. Creating the new link under another name and renaming it over the old one
# is a single rename(2), which either happens or does not.
#
# If either step fails, the old symlink is still what it was, so the site can be put
# back exactly as it was -- and it is, here, rather than left stopped by the caller's
# `set -e` for the sake of an error message.
if ! ln -sfn "${INSTALL_DIR}" "${OPUS_DIR}/deployed.new" ||
   ! mv -Tf "${OPUS_DIR}/deployed.new" "${OPUS_DIR}/deployed"; then
    echo "ERROR: could not switch ${OPUS_DIR}/deployed to ${INSTALL_DIR}."
    echo "       Restarting what was running before."
    sudo systemctl start "${OPUS_WEB_SERVICE}"
    exit 1
fi

# Restarting the cache service is how the shared cache is emptied: it holds rendered
# results and search results computed by the release that is being replaced, and a
# cache key does not say which release wrote it. The process-local caches inside each
# worker go with the workers that are about to be started.
#
# Its failure is reported rather than fatal, because the caller runs under `set -e`
# and stopping here would leave the site down with the switch already made. An
# installation with no shared cache falls back to a per-worker one, which the restart
# below empties anyway, and says so by leaving OPUS_CACHE_SERVICE empty.
if [[ -n ${OPUS_CACHE_SERVICE} ]]; then
    if ! sudo systemctl restart "${OPUS_CACHE_SERVICE}"; then
        echo "WARNING: ${OPUS_CACHE_SERVICE} did not restart. If this installation"
        echo "         uses it, the shared cache still holds entries the previous"
        echo "         release wrote."
    fi
fi

sudo systemctl start "${OPUS_WEB_SERVICE}"

echo
echo "Now serving: ${OPUS_DIR}/deployed -> $(readlink "${OPUS_DIR}/deployed")"
