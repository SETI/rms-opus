#!/bin/bash
# This script is in a separate file from import_all.sh so that we can use nohup on it and yet make the
# original import_all.sh interactive.
python main_opus_import.py --drop-permanent-tables --scorched-earth --override-db-schema $1
python main_opus_import.py --import-check-duplicate-id --do-all-import --override-db-schema $1 GALILEO
python main_opus_import.py --import-check-duplicate-id --do-all-import --override-db-schema $1 HST
python main_opus_import.py --import-check-duplicate-id --do-all-import --override-db-schema $1 NEWHORIZONS --exclude-volumes NHKCLO1001,NHKCLO_2001,NHKELO_1001,NHKELO_2001,NHKCMV1001,NHKCMV_2001,NHKEMV_1001,NHKEMV_2001
python main_opus_import.py --import-check-duplicate-id --do-all-import --override-db-schema $1 COVIMS
python main_opus_import.py --import-check-duplicate-id --do-all-import --override-db-schema $1 COUVIS
python main_opus_import.py --do-all-import --override-db-schema $1 VOYAGER
python main_opus_import.py --do-all-import --override-db-schema $1 COCIRS
python main_opus_import.py --do-all-import --override-db-schema $1 COISS
python main_opus_import.py --cleanup-aux-tables --override-db-schema $1
python main_opus_import.py --import-dictionary --override-db-schema $1
python main_opus_import.py --validate-perm --override-db-schema $1

echo "Import is complete!"
sqldump=/home/django/database_backups/$1.sql
echo "Making backup of database - Dumping $1 to $sqldump"
mysqldump $1 $2 > $sqldump
echo "Making dev_$1 version of database"
echo "CREATE DATABASE dev_$1;" | mysql $2
mysql dev_$1 $2 < $sqldump
echo "NOTE: You must change opus_secrets.py and then run 'python manage.py migrate' before use"
