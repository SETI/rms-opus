#!/bin/sh
# Usage: clone_database.sh dbname1 dbname2 "MySQL params"
# Example: clone_database.sh opus3_191205 dev_opus3_191205 "-urfrench -p -h tools2.pds-rings.seti.org"
echo "***" Cloning $1 to $2
sqldump=/tmp/$1.sql
echo Dumping $1 to $sqldump
mysqldump $1 $3 > $sqldump
echo "CREATE DATABASE $2;" | mysql $3
echo Creating clone $2
mysql $2 $3 < $sqldump
