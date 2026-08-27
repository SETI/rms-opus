# This file should only be used with "source"
#
# Create one OPUS installation: a directory holding a virtualenv with the rms-opus
# distribution installed from PyPI, and the opus.toml that installation reads.
#
# There is no checkout here. The application, the import pipeline and the log
# analyzer are all installed packages, and their programs are the console scripts
# the distribution declares (opus_import, opus_log_analyzer, opus_error_analyzer),
# so nothing in the chain below needs a repository-relative path or a `cd` into a
# source tree. The only checkout on the server is the one holding these scripts.
#
# Inputs (exported by the caller): OPUS_SRC_DIR, OPUS_DIR_NAME, OPUS_DB_NAME,
# OPUS_LOG_DIR and everything _read_deploy_env.sh exports. OPUS_VERSION_SPEC is
# optional and is appended to the distribution name, e.g. "==3.23.0".
#
# Exports: OPUS_CONFIG, pointing at the opus.toml written here. This file is
# sourced, so that export reaches every later step of the deploy.

if [[ ! -v OPUS_SRC_DIR ]]; then
    echo "INTERNAL ERROR: OPUS_SRC_DIR undefined"
    exit 1
fi

if [[ ! -v OPUS_DIR_NAME ]]; then
    echo "INTERNAL ERROR: OPUS_DIR_NAME undefined"
    exit 1
fi

if [[ ! -v IMPORT_SCRIPT_DIR ]]; then
    echo "INTERNAL ERROR: IMPORT_SCRIPT_DIR undefined"
    exit 1
fi

cd ${OPUS_SRC_DIR}

if [[ -e ${OPUS_SRC_DIR}/${OPUS_DIR_NAME} ]]; then
    echo "INTERNAL ERROR: ${OPUS_SRC_DIR}/${OPUS_DIR_NAME} already exists"
    exit 1
fi

mkdir -p ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}
cd ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}

python3.12 -m venv opus_venv 2>&1
source opus_venv/bin/activate
python -m pip install --upgrade pip 2>&1

# The released distribution, from PyPI. OPUS_VERSION_SPEC pins a particular release
# ("==3.23.0"); with it empty, pip takes the newest. To reproduce an installation
# exactly, generate a constraints file from a known-good server --
# `python -m pip freeze > constraints.txt` inside its opus_venv -- and pass it here
# with `-c constraints.txt`; the deploy does not maintain one, because the floors in
# the distribution's own metadata are what this project supports.
python -m pip install "rms-opus${OPUS_VERSION_SPEC:-}" 2>&1

# Per-host application settings. Staging and production differ only in these.
if [[ $HOSTNAME =~ ^staging.*$ ]]; then
    export OPUS_DEBUG=true
    export OPUS_PUBLIC_URL=http://staging.pds.seti.org/
    export OPUS_PRODUCT_HTTP_PATH=http://staging.pds.seti.org/
    export OPUS_VIEWMASTER_URL=http://staging.pds.seti.org/
    export OPUS_TAR_FILE_URL=http://staging.pds.seti.org/downloads/
else
    export OPUS_DEBUG=false
    export OPUS_PUBLIC_URL=https://opus.pds-rings.seti.org/
    export OPUS_PRODUCT_HTTP_PATH=https://opus.pds-rings.seti.org/
    export OPUS_VIEWMASTER_URL=https://pds-rings.seti.org/
    export OPUS_TAR_FILE_URL=https://opus.pds-rings.seti.org/downloads/
fi
export OPUS_DB_NAME
export OPUS_LOG_DIR

${IMPORT_SCRIPT_DIR}/_write_opus_toml.sh ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/opus.toml

# The import pipeline and the web application are installed packages, so they locate
# the configuration by this variable instead of by the directory they happen to be
# invoked from. OPUS has no default path for it, by design: a server running several
# installations gives each one its own.
export OPUS_CONFIG=${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/opus.toml

# Django's own management commands need to know which settings module to use; the
# installed distribution has no manage.py to imply it.
export DJANGO_SETTINGS_MODULE=opus_app.settings

# A stable path for Apache's WSGIScriptAlias. The application's wsgi module lives
# inside the virtualenv's site-packages, whose path carries the Python minor
# version; this symlink is what lets the vhost name a path that never changes:
#
#     WSGIScriptAlias / ${OPUS_SRC_DIR}/rms-opus/wsgi.py
#
# See docs/dev_guide_deployment.rst for the whole vhost stanza.
ln -sfn "$(python -c 'import opus_app.wsgi; print(opus_app.wsgi.__file__)')" \
        ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/wsgi.py

echo
echo
echo "Installed rms-opus $(python -c 'import importlib.metadata as m; print(m.version("rms-opus"))')"
echo "OPUS_CONFIG: ${OPUS_CONFIG}"
echo "WSGI script: ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/wsgi.py -> $(readlink ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/wsgi.py)"
echo
echo "opus.toml:"
echo
cat opus.toml
