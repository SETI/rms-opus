#/bin/sh
(cd ../opus/application; python manage.py migrate)
(cd ../opus/application; yes yes | python manage.py collectstatic)
(cd ../opus/application; python clear_django_cache.py)
systemctl restart memcached
systemctl restart apache2
