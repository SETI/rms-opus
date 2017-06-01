import sys
import os
import django
from os.path import getsize
from django.conf import settings
from django.db import connection

nulls_only = True

# sys.path.append('/Users/lballard/projects/')
sys.path.append('/home/django/djcode/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opus.settings")
django.setup()
from secrets import IMAGE_PATH

from results.views import get_base_path_previews
from settings import opus_to_deploy

cursor = connection.cursor()

cursor.execute("use %s;" % opus_to_deploy)

sql = "select ring_obs_id, thumb, small, med, full from images"
if nulls_only:
    sql += "  where size_thumb is null or size_thumb = 0 or size_small is null or size_small = 0 or size_med is null or size_med = 0 or size_full is null or size_full = 0";
# sql += " limit 500"
print(sql)

cursor.execute(sql)

for row in cursor.fetchall():
    skip = False  # skip this row
    ring_obs_id, thumb, small, med, full = row
    all_img_paths = {'thumb': thumb, 'small': small, 'med': med, 'full': full}
    all_img_sizes = {'size_thumb': 0, 'size_small': 0, 'size_med': 0, 'size_full': 0}

    for size_name, img_path in all_img_paths.items():

        try:
            full_path = IMAGE_PATH + get_base_path_previews(ring_obs_id) + img_path
        except TypeError:
            print("Error: null for img path found by get_base_path_previews for:  %s" % ring_obs_id)
            print('Error ' + str(all_img_paths))
            skip = True

        try:
            size = getsize(full_path)
        except OSError:
            print("Error: Could not find file %s" % full_path)
            skip = True

        all_img_sizes['size_' + size_name] = size

    if not skip:
        # now we have all the sizes for this row, update the database
        sql_snippet = ', '.join(["%s = %i" % (size_name, img_size) for size_name, img_size in all_img_sizes.items()])
        sql_up = "update images set %s where ring_obs_id = '%s' " % (sql_snippet, ring_obs_id)
        print(sql_up)
        cursor.execute(sql_up)
            continue

        all_img_sizes['size_' + size_name] = size

    # now we have all the sizes for this row, update the database
    sql_snippet = ', '.join(["%s = %i" % (size_name, img_size) for size_name, img_size in all_img_sizes.items()])
    sql_up = "update images set %s where ring_obs_id = '%s' " % (sql_snippet, ring_obs_id)
    print(sql_up)
    cursor.execute(sql_up)

print("OK BYE! ")
