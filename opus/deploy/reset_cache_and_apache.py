#/bin/sh
(cd ../application; yes yes | python manage.py collectstatic)
(cd ../application; python clear_django_cache.py)
systemctl restart memcached
systemctl restart apache2
