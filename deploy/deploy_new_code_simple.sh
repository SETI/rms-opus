#/bin/sh
#
# We assume a directory structure like:
# .../opus/src/pds-opus
# .../opus/opus_venv
#
source ../../../opus_venv/bin/activate
sudo systemctl stop apache2
(cd ../opus/application; yes yes | python manage.py collectstatic)
(cd ../opus/application; python clear_django_cache.py)
(cd ../opus/import; python main_opus_import.py --create-param-info --create-partables --create-table-names --create-grouping-target-name --import-dict)
sudo systemctl restart memcached
sudo systemctl start apache2
