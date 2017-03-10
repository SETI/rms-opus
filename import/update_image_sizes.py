import sys
import os
import django
from os.path import getsize
from django.conf import settings
from django.db import connection
from secrets import DEPLOYMENT_PARENT_DIR

nulls_only = True

# sys.path.append('/Users/lballard/projects/')
sys.path.append(DEPLOYMENT_PARENT_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opus.settings")
django.setup()
from secrets import IMAGE_PATH
from results.views import get_base_path_previews

cursor = connection.cursor()

sql = "select ring_obs_id, thumb, small, med, full from images"
if nulls_only:
    sql += " where size_thumb is null or size_small is null or size_med is null or size_full is null"
# sql += " limit 500"
print(sql)

cursor.execute(sql)

for row in cursor.fetchall():
    ring_obs_id, thumb, small, med, full = row
    all_img_paths = {'thumb': thumb, 'small': small, 'med': med, 'full': full}
    all_img_sizes = {'size_thumb': 0, 'size_small': 0, 'size_med': 0, 'size_full': 0}

    for size_name, img_path in all_img_paths.items():
        full_path = IMAGE_PATH + get_base_path_previews(ring_obs_id) + img_path

        try:
            size = getsize(full_path)

        except OSError:
            print("Error: Could not find file %s" % full_path)

        all_img_sizes['size_' + size_name] = size

    # now we have all the sizes for this row, update the database
    sql_snippet = ', '.join(["%s = %i" % (size_name, img_size) for size_name, img_size in all_img_sizes.items()])
    sql_up = "update_images set %s where ring_obs_id = '%s' " % (sql_snippet, ring_obs_id)
    print(sql_up)
    # cursor.execute(sql_up)

print("OK BYE! ")
