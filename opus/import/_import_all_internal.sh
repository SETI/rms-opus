#!/bin/bash
# This script is in a separate file from import_all.sh so that we can use nohup on it and yet make the
# original import_all.sh interactive.

# Destroy the current database
python main_opus_import.py --drop-permanent-tables --scorched-earth --override-db-schema $1 $3

# Start with volumes that require duplicate ID checks to make them run faster
python main_opus_import.py --import-check-duplicate-id --do-all-import --override-db-schema $1 $3 GALILEO

# Other normal volumes, more or less in reverse order of time to import
python main_opus_import.py --do-all-import --override-db-schema $1 $3 EBROCC
python main_opus_import.py --do-all-import --override-db-schema $1 $3 COUVIS_8xxx
python main_opus_import.py --do-all-import --override-db-schema $1 $3 COVIMS_8xxx
python main_opus_import.py --do-all-import --override-db-schema $1 $3 CORSS_8xxx
python main_opus_import.py --do-all-import --override-db-schema $1 $3 VOYAGER
python main_opus_import.py --do-all-import --override-db-schema $1 $3 NEWHORIZONS
python main_opus_import.py --do-all-import --override-db-schema $1 $3 HST
python main_opus_import.py --do-all-import --override-db-schema $1 $3 COCIRS
python main_opus_import.py --do-all-import --override-db-schema $1 $3 COISS
python main_opus_import.py --do-all-import --override-db-schema $1 $3 COUVIS_0xxx
python main_opus_import.py --do-all-import --override-db-schema $1 $3 COVIMS_0xxx

python main_opus_import.py --cleanup-aux-tables --override-db-schema $1
python main_opus_import.py --import-dictionary --override-db-schema $1
python main_opus_import.py --validate-perm --override-db-schema $1

echo "Import is complete!"
# sqldump=/Volumes/opus/databases/$1.sql
# echo "Making backup of database - Dumping $1 to $sqldump"
# mysqldump $1 $2 > $sqldump
# echo "Making dev_$1 version of database"
# echo "CREATE DATABASE dev_$1;" | mysql $2
# mysql dev_$1 $2 < $sqldump
# echo "NOTE: You must change opus_secrets.py and then run 'python manage.py migrate' before use"
