#!/bin/sh
python main_opus_import.py --import-check-duplicate-id --do-it-all GALILEO $1
python main_opus_import.py --import-check-duplicate-id --do-it-all HST --exclude-volumes HSTJ0_9391 $1
python main_opus_import.py --import-check-duplicate-id --do-it-all NEWHORIZONS $1
python main_opus_import.py --import-check-duplicate-id --do-it-all COVIMS $1
python main_opus_import.py --import-check-duplicate-id --do-it-all COUVIS $1
python main_opus_import.py --do-it-all VOYAGER $1
python main_opus_import.py --do-it-all COCIRS $1
python main_opus_import.py --do-it-all COISS $1
python main_opus_import.py --import-dictionary
