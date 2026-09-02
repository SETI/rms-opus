# This file should only be used with "source"
#
# Create one OPUS installation: a directory holding a virtualenv with the rms-opus
# distribution installed from PyPI, and the opus.toml that installation reads.
#
# It is built under ${OPUS_DIR}/staged, beside whatever is being served, and nothing
# here touches the running installation. What makes a staged installation the served
# one is _promote.sh, and until that runs the site is unaffected by anything this
# builds -- including a failure half way through it.
#
# There is no checkout here. The application, the import pipeline and the log
# analyzer are all installed packages, and their programs are the console scripts
# the distribution declares (opus_import, opus_log_analyzer, opus_error_analyzer,
# and opus_manage for Django's own management commands), so nothing in the chain
# below needs a repository-relative path or a `cd` into a source tree. These scripts
# were written out of an installed distribution by opus_deploy_scripts, so there is no
# checkout on the server at all.
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

if [[ ! -v OPUS_DIR ]]; then
    echo "INTERNAL ERROR: OPUS_DIR undefined"
    exit 1
fi

cd ${OPUS_SRC_DIR}

if [[ -e ${OPUS_SRC_DIR}/${OPUS_DIR_NAME} ]]; then
    echo "INTERNAL ERROR: ${OPUS_SRC_DIR}/${OPUS_DIR_NAME} already exists"
    exit 1
fi

mkdir -p ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}
cd ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}

${OPUS_PYTHON} -m venv opus_venv 2>&1

# The deploy chain's own environment is active at this point, and everything after
# this line -- opus_import, opus_manage, pip -- has to be this installation's rather
# than that one's. Leaving both active would put two releases of the same console
# scripts on PATH and settle it by ordering.
if [[ -n ${VIRTUAL_ENV:-} ]] && type deactivate > /dev/null 2>&1; then
    deactivate
fi
source opus_venv/bin/activate
python -m pip install --upgrade pip 2>&1

# The released distribution, from PyPI. OPUS_VERSION_SPEC pins a particular release
# ("==3.23.0"); with it empty, pip takes the newest. One of the dependencies this
# pulls in is not from PyPI -- rms-opus asks for the rewrite branch of rms-pdsfile by
# its repository URL -- so this step needs git on the machine and a network path to
# GitHub. To reproduce an installation
# exactly, generate a constraints file from a known-good server --
# `python -m pip freeze > constraints.txt` inside its opus_venv -- and pass it here
# with `-c constraints.txt`; the deploy does not maintain one, because the floors in
# the distribution's own metadata are what this project supports.
python -m pip install "rms-opus${OPUS_VERSION_SPEC:-}" 2>&1

# The memcached client. It is not a dependency of the distribution -- OPUS runs
# without it, on Django's per-process local-memory cache -- but a server wants the
# shared one: it is what several worker processes answer from, and it is what the
# switch at the end of a deploy empties by restarting memcached. Without this
# package installed, that restart clears nothing, and each worker goes on answering
# from its own memory. Installed per installation because that is where the
# application imports it from, and it is only ever imported if memcached itself is
# running.
python -m pip install pymemcache 2>&1

# What this installation says about itself -- its URLs, its debug flag, the hosts it
# answers to, its cache prefix -- comes from deploy.env, which _read_deploy_env.sh has
# already read and exported. Choosing them here, from the host name, is what this used
# to do, and it meant every server's addresses were written into a script that ships to
# every server.
export OPUS_DB_NAME
export OPUS_LOG_DIR

# The directories the generated opus.toml names outside this installation. They belong
# to the server rather than to any one installation -- every installation writes cart
# archives and static files to the same places -- and they are created here because
# this is what writes the configuration that names them. OPUS_DIR, from deploy.env, is
# the only place any of these paths comes from.
#
# The application opens its log file as it starts, and builds a cart archive into
# tar_dir on demand, so a directory missing here is a deploy that succeeds and a site
# that fails later.
mkdir -p "${OPUS_DIR}/opus_logs"
mkdir -p "${OPUS_DIR}/downloads"
mkdir -p "${OPUS_DIR}/manifests"
mkdir -p "${OPUS_DIR}/static_media"

"${IMPORT_SCRIPT_DIR}/_write_opus_toml.sh" "${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/opus.toml"

# The import pipeline and the web application are installed packages, so they locate
# the configuration by this variable instead of by the directory they happen to be
# invoked from. OPUS has no default path for it, by design: a server running several
# installations gives each one its own.
export OPUS_CONFIG=${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/opus.toml

# That is the whole environment. Django's management commands are run as
# `opus_manage`, which names the settings module itself, so DJANGO_SETTINGS_MODULE
# is nobody's to export here.

# A stable path for Apache's WSGIScriptAlias. The application's wsgi module lives
# inside the virtualenv's site-packages, whose path carries the Python minor
# version; this symlink is what lets the vhost name a path that never changes,
# through the deployed symlink:
#
#     WSGIScriptAlias / ${OPUS_DIR}/deployed/wsgi.py
#
# The whole vhost stanza is in the User Guide:
# https://rms-opus.readthedocs.io/en/latest/user_guide_web_server.html
#
# find_spec locates the file WITHOUT importing it. Importing opus_app.wsgi runs
# get_wsgi_application(), which calls django.setup() and opens the log file, so it
# fails whenever the environment is not fully ready -- and this step runs before the
# log directory is guaranteed to exist. Such a failure is silent in the worst way: the
# command substitution returns empty, `ln` is handed an empty target, and the deploy
# dies here with Apache already stopped. The guard below is what makes it loud.
OPUS_WSGI_PATH=$(python -c \
    'import importlib.util; print(importlib.util.find_spec("opus_app.wsgi").origin)')
if [[ -z ${OPUS_WSGI_PATH} || ! -f ${OPUS_WSGI_PATH} ]]; then
    echo "ERROR: cannot locate opus_app/wsgi.py in the installed distribution."
    echo "       Apache's WSGIScriptAlias target cannot be created."
    exit 1
fi
ln -sfn "${OPUS_WSGI_PATH}" ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/wsgi.py

echo
echo
echo "Installed rms-opus $(python -c 'import importlib.metadata as m; print(m.version("rms-opus"))')"
echo "OPUS_CONFIG: ${OPUS_CONFIG}"
echo "WSGI script: ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/wsgi.py -> $(readlink ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/wsgi.py)"
echo
echo "opus.toml:"
echo
cat opus.toml
