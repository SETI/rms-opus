from django.shortcuts import get_object_or_404
import settings



def error_log(msg):
    import datetime

    path = settings.ERROR_LOG_PATH


