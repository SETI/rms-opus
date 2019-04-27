#!/bin/sh
echo "Note: Database sysbench_test must already exist"
sysbench --test=oltp --oltp-table-size=1000000 --mysql-db=sysbench_test --mysql-user=rfrench "--mysql-password=$1" prepare
