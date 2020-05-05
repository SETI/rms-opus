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
python main_opus_import.py --drop-permanent-tables --scorched-earth
python main_opus_import.py --do-all-import COISS_2002,COISS_2008,COISS_2111
python main_opus_import.py --do-all-import COUVIS_0002
python main_opus_import.py --do-all-import COVIMS_0006
python main_opus_import.py --do-all-import COCIRS_5408
python main_opus_import.py --do-all-import GO_0017
python main_opus_import.py --do-all-import VGISS_6210,VGISS_8201
python main_opus_import.py --do-all-import HSTI1_1559,HSTI1_2003,HSTJ0_9975,HSTN0_7243,HSTO0_7308,HSTU0_5642
python main_opus_import.py --do-all-import NHPELO_2001,NHLAMV_2001
python main_opus_import.py --do-all-import EBROCC_0001
python main_opus_import.py --do-all-import CORSS_8001
python main_opus_import.py --do-all-import COUVIS_8001
python main_opus_import.py --cleanup-aux-tables
python main_opus_import.py --import-dictionary
(cd ../application; python manage.py migrate)
python main_opus_import.py --validate-perm
