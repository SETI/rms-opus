#!/bin/bash
# Usage: clone_database.sh dbname1 dbname2 "MySQL params"
# Example: clone_database.sh opus3_191205 dev_opus3_191205 "-u<user> -p -h <db host>"
#
# mysqldump writes each view with the account that defined it, and creating a view
# defined by another account needs the SET_USER_ID privilege. The load drops that DEFINER
# clause from each view, so the account running it defines the views itself. OPUS's
# views are SQL SECURITY INVOKER, so the definer decides nothing. A dump made from
# inside the database names no schema in a view, so the views read the clone's tables.
#
# Each step stops the clone when it fails: a failed dump creates no target, and a failed
# load exits with failure. The dump file is removed whichever way the script ends.
set -o pipefail
echo "***" Cloning $1 to $2
sqldump=$(mktemp) || exit 1
trap 'rm -f "$sqldump"' EXIT
echo Dumping $1 to $sqldump
mysqldump $1 $3 > "$sqldump" || exit 1
echo "CREATE DATABASE $2;" | mysql $3 || exit 1
echo Creating clone $2
sed -e '/^\/\*!50013 DEFINER=/s/ DEFINER=`[^`]*`@`[^`]*`//' "$sqldump" | mysql $2 $3
