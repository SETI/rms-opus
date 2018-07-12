from django.conf import settings # import the settings file

"""
 if you want a setting variable to be available in any UI templates, define them in here:
"""
def admin_media(context):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
        'ADMIN_MEDIA_PREFIX':settings.ADMIN_MEDIA_PREFIX,
        'MEDIA_URL':settings.MEDIA_URL,
        'DEFAULT_PAGE_LIMIT': settings.DEFAULT_PAGE_LIMIT,
        'PRODUCT_HTTP_PATH':settings.PRODUCT_HTTP_PATH
        }
