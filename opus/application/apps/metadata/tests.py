# metadata/test.py

import json
import sys
from unittest import TestCase

from django.db import connection
from django.test.client import Client

from metadata.views import *

import logging
log = logging.getLogger(__name__)

settings.CACHE_BACKEND = 'dummy:///'

class MetadataTests(TestCase):

    # Functions that need unit testing:
    # get_fields_info

    pass
