# Set up the Django Enviroment for running as shell script
import sys
sys.path.append('/home/django/djcode/opus')  #srvr
# sys.path.append('/users/lballard/projects/opus/')
# from opus import settings
from django.conf import settings
from settings import CACHES, DATABASES  # DATABASES creds only
settings.configure(CACHES=CACHES, DATABASES=DATABASES) # include any other settings you might need

# script imports
from os import system
from django.db import connection
sys.path.append("/home/django/djcode/opus/")

if len(sys.argv) < 2:
    print "please pass database name as first arg"
    sys.exit()

database_name = sys.argv[1]

cursor = connection.cursor()

manifest_file_list = "/home/lballard/metrics/manifest_list.txt"
base_path_manifests = "/usr/share/nginx/www/opus/"

manifest_files = [line.strip() for line in open(manifest_file_list, 'r')]

inst_counts = {'COISS':0,'COVIMS':0,'GOSSI':0,'LORRI':0,'COCIRS':0,'VGISS':0,'COUVIS':0}
inst_sizes = {'COISS':0,'COVIMS':0,'GOSSI':0,'LORRI':0,'COCIRS':0,'VGISS':0,'COUVIS':0}


def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

for f in manifest_files:

    all_downloaded_files = []
    for line in open(base_path_manifests + f, 'r'):
        try:
            all_downloaded_files.append((line.strip().split(':')[0].strip(), line.strip().split(':')[1].strip()))
        except IndexError:
            continue

    for file_info in all_downloaded_files:
        rid, file_name = file_info

	inst = ''

        if rid.find('CO_ISS') > -1:
            inst = 'COISS'

        if rid.find('CO_VIMS') > -1:
            inst = 'COVIMS'

        if rid.find('GO_SSI') > -1:
            inst = 'COVIMS'

        if rid.find('NH_LORRI') > -1:
            inst = 'LORRI'

        if rid.find('CO_CIRS') > -1:
            inst = 'COCIRS'

        if rid.find('VG1_ISS') > -1:
            inst = 'VGISS'

        if rid.find('VG2_ISS') > -1:
            inst = 'VGISS'

        if rid.find('CO_UVIS') > -1:
            inst = 'COUVIS'

        if inst:
            inst_counts[inst] += 1

            try:
                if file_name.lower().find('jpg') == -1 and file_name.lower().find('png') == -1:
                    q_size = "select size from file_sizes where ring_obs_id = '%s' and file_name = '%s'" % file_info
                    cursor.execute(q_size)
                    size = cursor.fetchone()[0]
                    inst_sizes[inst] += int(size)
            except TypeError:
                print "--- type error above, no size added yo ------ \n " + q_size
                print "found in " + base_path_manifests + f
                """
                I'm putting in a pass here becuase of issue # 128
                but really we should have it stop and investigate what is happening
                (import sys; sys.exit())
                import sys
                sys.exit()
                """
                pass

cursor.close()


x = [count for inst, count in inst_counts.items()]
print "Total Files Downloaded: " + str(sum(x)) + "\n"

print "Downloads by Instrument:"
for inst,count in inst_counts.items():
    print "\n" + inst + ":"
    print "    Files Downloaded: " + str(count)
    print "    Total Size: " + sizeof_fmt(inst_sizes[inst])


