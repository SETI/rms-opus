#/bin/sh
systemctl stop apache2
(cd ../opus/application; yes yes | python manage.py collectstatic)
(cd ../opus/application; python clear_django_cache.py)
systemctl restart memcached
systemctl start apache2
