coverage run ../../lib/opus_support.py
if [ $? -ne 0 ]; then exit -1; fi
coverage run -a manage.py $1 test -b
if [ $? -ne 0 ]; then exit -1; fi
coverage xml
if [ $? -ne 0 ]; then exit -1; fi
coverage html
if [ $? -ne 0 ]; then exit -1; fi
coverage report
