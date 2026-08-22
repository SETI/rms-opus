#!/bin/bash
# This script is in a separate file from import_all.sh so that we can use nohup on it and yet make the
# original import_all.sh interactive. Like import_all.sh, it runs from the root of the
# repository with rms-opus installed in the active environment.

# Destroy the current database
python -m opus_import --drop-permanent-tables --scorched-earth --override-db-schema $1 $3
if [ $? -ne 0 ]; then exit -1; fi

# Start with volumes that require duplicate ID checks to make them run faster
python -m opus_import --import-check-duplicate-id --do-all-import --override-db-schema $1 $3 GALILEO
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --import-check-duplicate-id --do-all-import --override-db-schema $1 $3 NEWHORIZONS
if [ $? -ne 0 ]; then exit -1; fi

# Other normal volumes, more or less in reverse order of time to import
python -m opus_import --do-all-import --override-db-schema $1 $3 EBROCC
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 uranus_occs_earthbased
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 cassini_uvis_solarocc_beckerjarmak2023
# if [ $? -ne 0 ]; then exit -1; fi
# python -m opus_import --do-all-import --override-db-schema $1 $3 cassini_iss_fring_mosaics_rsfrench2025
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 COUVIS_8xxx
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 COVIMS_8xxx
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 CORSS_8xxx
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 VOYAGER
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 HST
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 COCIRS
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 COISS
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 COUVIS_0xxx
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --do-all-import --override-db-schema $1 $3 COVIMS_0xxx
if [ $? -ne 0 ]; then exit -1; fi

python -m opus_import --cleanup-aux-tables --override-db-schema $1
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --import-dictionary --override-db-schema $1
if [ $? -ne 0 ]; then exit -1; fi
python -m opus_import --validate-perm --override-db-schema $1
if [ $? -ne 0 ]; then exit -1; fi

echo "Import is complete!"
# sqldump=/Volumes/opus/databases/$1.sql
# echo "Making backup of database - Dumping $1 to $sqldump"
# mysqldump $1 $2 > $sqldump
# echo "Making dev_$1 version of database"
# echo "CREATE DATABASE dev_$1;" | mysql $2
# mysql dev_$1 $2 < $sqldump
# echo "NOTE: You must change opus.toml and then run 'python manage.py migrate' before use"
