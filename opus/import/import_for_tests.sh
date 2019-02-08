#!/bin/sh
python main_opus_import.py --drop-permanent-tables --scorched-earth
python main_opus_import.py --do-all-import --import-fake-images COISS_2002,COISS_2008,COISS_2111
python main_opus_import.py --do-all-import --import-fake-images COUVIS_0002
python main_opus_import.py --do-all-import --import-fake-images COVIMS_0006
python main_opus_import.py --do-all-import --import-fake-images COCIRS_5408
python main_opus_import.py --do-all-import --import-fake-images GO_0017
python main_opus_import.py --do-all-import --import-fake-images VGISS_6210,VGISS_8201
python main_opus_import.py --do-all-import --import-fake-images HSTI1_1559,HSTI1_2003
python main_opus_import.py --do-all-import --import-fake-images HSTJ0_9975,HSTN0_7243,HSTO0_7308,HSTU0_5642
python main_opus_import.py --do-all-import --import-fake-images NHPELO_2001,NHLAMV_2001
python main_opus_import.py --cleanup-aux-tables
python main_opus_import.py --import-dictionary
(cd ../application; python manage.py migrate)
python main_opus_import.py --validate-perm
