import sys
import os
import django
from os.path import getsize
from django.conf import settings
from django.db import connection
from config import DB_NEW_IMPORT

nulls_only = True

# sys.path.append('/Users/lballard/projects/')
sys.path.append('/home/django/djcode/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opus.settings")
django.setup()
from secrets import IMAGE_PATH
from results.views import get_base_path_previews

cursor = connection.cursor()

cursor.execute("use %s;" % DB_NEW_IMPORT)

sql = "select ring_obs_id, thumb, small, med, full from {}.images ".format(DB_NEW_IMPORT)
if nulls_only:
    sql += "  where size_thumb is null or size_thumb = 0 or size_small is null or size_small = 0 or size_med is null or size_med = 0 or size_full is null or size_full = 0";
# sql += " limit 500"
print(sql)

cursor.execute(sql)

for row in cursor.fetchall():
    ring_obs_id, thumb, small, med, full = row
    all_img_paths = {'thumb': thumb, 'small': small, 'med': med, 'full': full}
    all_img_sizes = {'size_thumb': 0, 'size_small': 0, 'size_med': 0, 'size_full': 0}

    for size_name, this_img_path in all_img_paths.items():

        try:
            full_path = IMAGE_PATH + get_base_path_previews(ring_obs_id) + this_img_path
        except TypeError:
            print("Error: get_base_path previews returned None for %s" % ring_obs_id)
            continue

        try:
            size = getsize(full_path)

        except OSError:
            print("Error: Could not find file %s" % full_path)
            continue

        all_img_sizes['size_' + size_name] = size

    # now we have all the sizes for this row, update the database
    sql_snippet = ', '.join(["%s = %s" % (size_name, str(img_size)) for size_name, img_size in all_img_sizes.items()])
    sql_up = "update {}.images set {} where ring_obs_id = '{}' ".format(DB_NEW_IMPORT, sql_snippet, ring_obs_id)
    print(sql_up)
    cursor.execute(sql_up)

print("OK BYE! ")
