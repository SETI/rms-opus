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
python main_opus_import.py --do-all-import --import-use-row-files COISS_2002,COISS_2008,COISS_2111 $1
python main_opus_import.py --do-all-import --import-use-row-files COUVIS_0002 $1
python main_opus_import.py --do-all-import --import-use-row-files COVIMS_0006 $1
python main_opus_import.py --do-all-import --import-use-row-files COCIRS_5408 $1
python main_opus_import.py --do-all-import --import-use-row-files GO_0017 $1
python main_opus_import.py --do-all-import --import-use-row-files VGISS_6210,VGISS_8201 $1
python main_opus_import.py --do-all-import --import-use-row-files HSTI1_1559,HSTI1_2003,HSTJ0_9975,HSTN0_7243,HSTO0_7308,HSTU0_5642 $1
python main_opus_import.py --do-all-import --import-use-row-files NHPELO_2001,NHLAMV_2001 $1
python main_opus_import.py --do-all-import --import-use-row-files EBROCC_0001 $1
python main_opus_import.py --do-all-import --import-use-row-files CORSS_8001 $1
python main_opus_import.py --do-all-import --import-use-row-files COUVIS_8001 $1
python main_opus_import.py --do-all-import --import-use-row-files COVIMS_8001 $1
python main_opus_import.py --cleanup-aux-tables
python main_opus_import.py --import-dictionary
(cd ../application; python manage.py migrate)
python main_opus_import.py --validate-perm
