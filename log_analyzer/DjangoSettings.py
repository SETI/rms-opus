import os

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'DIRS': [
        PROJECT_ROOT + '/templates/',
    ],
}]

SECRET_KEY = 'secret key'
