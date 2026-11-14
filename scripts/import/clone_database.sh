#!/bin/sh
# Usage: clone_database.sh dbname1 dbname2 "MySQL params"
# Example: clone_database.sh opus3_191205 dev_opus3_191205 "-u<user> -p -h <db host>"
echo "***" Cloning $1 to $2
sqldump=/tmp/$1.sql
echo Dumping $1 to $sqldump
mysqldump $1 $3 > $sqldump
echo "CREATE DATABASE $2;" | mysql $3
echo Creating clone $2
if [ ! -r $sqldump ]; then echo "Cannot read $sqldump" >&2; exit 1; fi
# The dump's FULLTEXT keys are built as the clone loads, keeping this session's stopword
# setting; the import builds them with the list off, so the clone does too.
{ echo 'SET SESSION innodb_ft_enable_stopword = OFF;'; cat $sqldump; } | mysql $2 $3
