#!/bin/sh
python main_opus_import.py --drop-permanent-tables --scorched-earth
python main_opus_import.py --import-check-duplicate-id --do-all-import GALILEO $1
python main_opus_import.py --import-check-duplicate-id --do-all-import HST --exclude-volumes HSTJ0_9391 $1
python main_opus_import.py --import-check-duplicate-id --do-all-import NEWHORIZONS $1
python main_opus_import.py --import-check-duplicate-id --do-all-import COVIMS $1
python main_opus_import.py --import-check-duplicate-id --do-all-import COUVIS $1
python main_opus_import.py --do-all-import VOYAGER $1
python main_opus_import.py --do-all-import COCIRS $1
python main_opus_import.py --do-all-import COISS $1
python main_opus_import.py --cleanup-aux-tables
python main_opus_import.py --import-dictionary
(cd ../application; python manage.py migrate)
python main_opus_import.py --validate-perm
