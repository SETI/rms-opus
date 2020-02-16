#/bin/sh
systemctl stop apache2
(cd ../opus/application; python manage.py migrate)
(cd ../opus/application; yes yes | python manage.py collectstatic)
(cd ../opus/application; python clear_django_cache.py)
(cd ../opus/import; python main_opus_import.py --import-dict --clean)
systemctl restart memcached
systemctl start apache2
