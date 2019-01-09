#!/bin/sh
python main_opus_import.py --drop-permanent-tables --scorched-earth
python main_opus_import.py --do-it-all --import-fake-images COISS_2002,COISS_2008,COISS_2111
python main_opus_import.py --do-it-all --import-fake-images COUVIS_0002
python main_opus_import.py --do-it-all --import-fake-images COVIMS_0006
python main_opus_import.py --do-it-all --import-fake-images GO_0017
python main_opus_import.py --do-it-all --import-fake-images VGISS_6210,VGISS_8201
python main_opus_import.py --do-it-all --import-fake-images HSTI1_1559,HSTI1_2003
python main_opus_import.py --import-dictionary
(cd ../application; python manage.py migrate)
