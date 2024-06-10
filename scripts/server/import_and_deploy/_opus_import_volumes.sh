# This file should only be used via "source"

cd ${OPUS_SRC_DIR}/${OPUS_DIR_NAME}/opus/import

set +e

echo "** DESTROY NEW DATABASE **"
echo
echo "Start time:" `date`
echo
python main_opus_import.py --drop-permanent-tables --scorched-earth > /dev/null 2>&1
if [ $? -ne 0 ]; then
    cat ${OPUS_LOG_DIR}/ERRORS.log
    exit -1
fi
echo

# Start with volumes that require duplicate ID checks to make them run faster

echo "** IMPORT GALILEO **"
echo
echo "Start time:" `date`
echo
python main_opus_import.py --import-check-duplicate-id --do-all-import GALILEO > /dev/null 2>&1
if [ $? -ne 0 ]; then
    cat ${OPUS_LOG_DIR}/ERRORS.log
    exit -1
fi
echo

# Other normal volumes, more or less in reverse order of time to import

for VOLUME in \
  EBROCC \
  uranus_occs_earthbased \
  COUVIS_8xxx \
  COVIMS_8xxx \
  CORSS_8xxx \
  VOYAGER \
  NEWHORIZONS \
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
    python main_opus_import.py --do-all-import ${VOLUME} > /dev/null 2>&1
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
python main_opus_import.py --cleanup-aux-tables > /dev/null 2>&1
if [ $? -ne 0 ]; then
    cat ${OPUS_LOG_DIR}/ERRORS.log
    exit -1
fi
echo

echo "** IMPORT DICTIONARY **"
echo
echo "Start time:" `date`
echo
python main_opus_import.py --import-dictionary > /dev/null 2>&1
if [ $? -ne 0 ]; then
    cat ${OPUS_LOG_DIR}/ERRORS.log
    exit -1
fi
echo

echo "** VALIDATE TABLES **"
echo
echo "Start time:" `date`
echo
python main_opus_import.py --validate-perm > /dev/null 2>&1
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
cd ../application
python manage.py migrate 2>&1
echo

echo
echo "End time:" `date`
echo
echo "** IMPORT COMPLETE **"
