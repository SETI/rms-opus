from django.conf import settings # import the settings file

"""
 if you want a setting variable to be available in any UI templates, define them in here:
"""
def admin_media(context):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
        'ADMIN_MEDIA_PREFIX':settings.ADMIN_MEDIA_PREFIX,
        'MEDIA_URL':settings.MEDIA_URL,
        'DEFAULT_LIMIT': settings.DEFAULT_LIMIT,
        'IMAGE_HTTP_PATH':settings.IMAGE_HTTP_PATH
        }