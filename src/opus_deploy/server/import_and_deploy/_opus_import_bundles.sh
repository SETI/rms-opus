# This file should only be used via "source"
#
# Import every bundle set into the database this staged installation names.
#
# `opus_import_all` is the console script the installed distribution declares, found
# on PATH through the activated virtualenv. It is the sequence itself -- the
# registration of every bundle set in order, the import, the auxiliary tables, the
# dictionary and the validation, each as its own `opus_import` process, stopping at the
# first failure -- so the order and the per-set options live in the release being
# installed rather than in a copy here that could disagree with it. The database is the
# one this installation just created for itself, so nothing needs erasing first.
#
# There is no `cd` into a source tree here: the pipeline is an installed package and
# locates its configuration through OPUS_CONFIG, which _opus_setup_environment.sh
# exported.

set +e

echo "** IMPORT ALL BUNDLE SETS **"
echo
echo "Start time:" `date`
echo
opus_import_all
if [ $? -ne 0 ]; then
    if [ -f ${OPUS_LOG_DIR}/ERRORS.log ]; then
        cat ${OPUS_LOG_DIR}/ERRORS.log
    fi
    exit -1
fi
echo

# A run that reached the end still has to be read: several import steps report a
# failure through the log and exit zero, so the log is the gate rather than the
# status.
if [ -s ${OPUS_LOG_DIR}/ERRORS.log ]; then
    echo "** THE IMPORT LOGGED ERRORS **"
    echo
    cat ${OPUS_LOG_DIR}/ERRORS.log
    exit -1
fi

set -e

echo "** MIGRATE **"
echo
echo "Start time:" `date`
echo
# Django's own contrib tables. `opus_manage` rather than `manage.py`: there is no
# checkout here and the wheel ships no manage.py. It is Django's own command line with
# the settings module already named, so OPUS_CONFIG is all it needs from the
# environment.
opus_manage migrate 2>&1
echo

echo
echo "End time:" `date`
echo
echo "** IMPORT COMPLETE **"
