#!/bin/sh
echo "*** DISK READ ***"
dd if=/dev/zero of=/tmp/ddtest.out bs=1G count=2 oflag=dsync
echo "*** DISK WRITE ***"
dd if=/tmp/ddtest.out of=/dev/null bs=1G count=2 oflag=dsync
rm /tmp/ddtest.out
