coverage run ../../lib/opus_support.py
coverage run -a manage.py $1 test -b
coverage html
coverage report
