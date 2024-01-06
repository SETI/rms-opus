#!/bin/bash -v -x

echo "*************************************************************"
echo "***** About to import TEST PDS DATA into a new database *****"
echo "*************************************************************"
echo
echo "About to ERASE and import to this database:"
grep "^DB_SCHEMA_NAME" ../../opus_secrets.py
echo "Note this should be the test-style name"
echo -n ">>> Type YES to continue: "
read yn
if [ "$yn" != "YES" ]; then
    echo "Aborting"
    exit 1
fi
python main_opus_import.py --drop-permanent-tables --scorched-earth $1
# python main_opus_import.py --do-all-import COISS_2002,COISS_2008,COISS_2111 $1
# python main_opus_import.py --do-all-import COUVIS_0002 $1
# python main_opus_import.py --do-all-import COVIMS_0006 $1
# python main_opus_import.py --do-all-import COCIRS_5408 $1
# python main_opus_import.py --import-check-duplicate-id --do-all-import GO_0016,GO_0017,GO_0018 $1
# python main_opus_import.py --do-all-import VGISS_6210,VGISS_8201 $1
# python main_opus_import.py --do-all-import HSTI1_3667,HSTI1_1559,HSTJ0_9975,HSTJ1_1085,HSTN0_7181,HSTO0_7316,HSTU0_5642 $1
# python main_opus_import.py --do-all-import NHPELO_1001,NHLAMV_1001,NHJUMV_1001 $1
# python main_opus_import.py --do-all-import EBROCC_0001 $1
# python main_opus_import.py --do-all-import CORSS_8001 $1
# python main_opus_import.py --do-all-import COUVIS_8001 $1
# python main_opus_import.py --do-all-import COVIMS_8001 $1
python main_opus_import.py --do-all-import VG_28xx $1
# python main_opus_import.py --do-all-import COCIRS_0406,COCIRS_1003 $1
# python main_opus_import.py --cleanup-aux-tables
# python main_opus_import.py --import-dictionary
# (cd ../application; python manage.py migrate)
# python main_opus_import.py --validate-perm

echo "ALL DONE!"

exit 0
