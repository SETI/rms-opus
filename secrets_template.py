# -*- coding: utf-8 -*-
# ⚠️ leaving any of these blank is catastrophic 🙅🏻
DB_USER = '<DB_USER>'
DB_PASS = '<DB_PASS>'
SECRET_KEY = '<SECRET_KEY>'  # Make unique, don't share
                             # can be generated https://www.google.com/search?q=django+secret+generator

# these all need trailing slashes
TAR_FILE_PATH =  '<TAR_FILE_PATH>'  # opus puts zipped cart files here for downloading
FILE_PATH  = '<FILE_PATH>'  # path pds data drive, typically named volumes/
DERIVED_PATH  = FILE_PATH + 'derived/'  # path to calibrated datasets
IMAGE_PATH = FILE_PATH + 'browse/'  # path to prevew images
