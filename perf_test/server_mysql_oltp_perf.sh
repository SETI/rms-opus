#!/bin/sh
sysbench --test=oltp --oltp-table-size=1000000 --oltp-test-mode=complex --oltp-read-only=off --num-threads=$1 --max-time=60 --max-requests=0 --mysql-db=sysbench_test --mysql-user=rfrench "--mysql-password=$2" run
