# This file should only be used via "source"
#
# `opus_import` is the console script the installed distribution declares, found on
# PATH through the activated virtualenv. There is no `cd` into a source tree here:
# the pipeline is an installed package and locates its configuration through
# OPUS_CONFIG, which _opus_setup_environment.sh exported.

set +e

echo "** DESTROY NEW DATABASE **"
echo
echo "Start time:" `date`
echo
opus_import --drop-permanent-tables --scorched-earth > /dev/null 2>&1
if [ $? -ne 0 ]; then
    cat ${OPUS_LOG_DIR}/ERRORS.log
    exit -1
fi
echo

# Start with volumes that require duplicate ID checks to make them run faster

for VOLUME in \
  GALILEO \
  NEWHORIZONS
do
    echo "** IMPORT ${VOLUME} **"
    echo
    echo "Start time:" `date`
    echo
    opus_import --import-check-duplicate-id --do-all-import ${VOLUME} > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        cat ${OPUS_LOG_DIR}/ERRORS.log
        exit -1
    fi
    echo
done

# Other normal volumes, more or less in reverse order of time to import.
#
# cassini_iss_fring_mosaics_rsfrench2025 is deliberately absent from the list below;
# it is disabled until its PDS4 shelf files exist. It cannot be commented out in
# place: a `#` line in the middle of a backslash continuation ENDS the continuation,
# which is a bash syntax error and made this entire script -- and with it the whole
# server import chain that sources it -- fail to parse. `bash -n` on this file is the
# check that catches it.

for VOLUME in \
  EBROCC \
  uranus_occs_earthbased \
  cassini_uvis_solarocc_beckerjarmak2023 \
  COUVIS_8xxx \
  COVIMS_8xxx \
  CORSS_8xxx \
  VOYAGER \
  HST \
  COCIRS \
  COISS \
  COUVIS_0xxx \
  COVIMS_0xxx
do
    echo "** IMPORT ${VOLUME} **"
    echo
    echo "Start time:" `date`
    echo
    opus_import --do-all-import ${VOLUME} > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        cat ${OPUS_LOG_DIR}/ERRORS.log
        exit -1
    fi
    echo
done

echo "** CREATE AUX TABLES **"
echo
echo "Start time:" `date`
echo
opus_import --cleanup-aux-tables > /dev/null 2>&1
if [ $? -ne 0 ]; then
    cat ${OPUS_LOG_DIR}/ERRORS.log
    exit -1
fi
echo

echo "** IMPORT DICTIONARY **"
echo
echo "Start time:" `date`
echo
opus_import --import-dictionary > /dev/null 2>&1
if [ $? -ne 0 ]; then
    cat ${OPUS_LOG_DIR}/ERRORS.log
    exit -1
fi
echo

echo "** VALIDATE TABLES **"
echo
echo "Start time:" `date`
echo
opus_import --validate-perm > /dev/null 2>&1
if [ $? -ne 0 ]; then
    cat ${OPUS_LOG_DIR}/ERRORS.log
    exit -1
fi
echo

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
