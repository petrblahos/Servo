# -*- coding: utf-8 -*-

import os
import re
import socket
from datetime import timedelta
from django.contrib.messages import constants as messages

DEBUG = False
TEMPLATE_DEBUG = DEBUG

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

BASE_DIR = os.path.dirname(__file__)
APP_DIR = os.path.join(BASE_DIR, 'servo')

ADMINS = (
    ('ServoApp Support', 'support@servoapp.com'),
)

MANAGERS = ADMINS

LANGUAGES = (
    ('da', 'Danish'),
    ('nl', 'Dutch'),
    ('en', 'English'),
    ('et', 'Estonian'),
    ('fi', 'Finnish'),
    ('sv', 'Swedish'),
)

SITE_ID = 1
USE_TZ = True
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = '/files/'

STATIC_ROOT = os.path.join(APP_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Absolute path to the directory that will hold temporary files.
TEMP_ROOT = os.path.join(MEDIA_ROOT, 'temp')

MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'servo.lib.middleware.LoginRequiredMiddleware',
    'servo.lib.middleware.TimezoneMiddleware',
    #'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'servo.urls.default'
SESSION_SERIALIZER = 'servo.lib.utils.SessionSerializer'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': (
            os.path.join(APP_DIR, 'templates'),
            os.path.join(BASE_DIR, 'uploads'),
        ),
        'OPTIONS': {
            'context_processors': (
                #'django.template.context_processors.debug',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.messages.context_processors.messages',
            ),
        }
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django.contrib.sessions',
    #'debug_toolbar',
    'rest_framework', 'wkhtmltopdf',
    'rest_framework.authtoken',
    'mptt', 'bootstrap3',
    'servo',
)

AUTH_USER_MODEL = 'servo.User'
AUTH_PROFILE_MODULE = 'servo.UserProfile'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'stderr': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

FILE_UPLOAD_HANDLERS = ("django_excel.ExcelMemoryFileUploadHandler",
                        "django_excel.TemporaryExcelFileUploadHandler",)

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
EXEMPT_URLS = []

LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'

# URLs that should work without logging in
LOGIN_EXEMPT_URLS = [
    LOGIN_URL.lstrip('/'),
    'register/$',
    'checkin/',
    'barcode/',
    'api/messages/',
    'api/status/',
    'api/warranty/',
    'api/orders/',
    'api/notes/',
    'api/users/',
    'api/customers/',
    'api/devices/'
]

# 404 URLs that should be ignored
IGNORABLE_404_URLS = [
    re.compile(r'favicon\.ico')
]

TEST_RUNNER = 'servo.tests.NoDbTestRunner'

EMAIL_HOST = 'mail.servoapp.com'
EMAIL_HOST_PASSWORD = ''
EMAIL_HOST_USER = ''
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = '[Servo] '
DEFAULT_FROM_EMAIL = 'support@servoapp.com'
SERVER_EMAIL = 'servo@' + socket.gethostname()

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

ENABLE_RULES = False
TIMEZONE = 'Europe/Helsinki'
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

GSX_CERT = os.path.join(BASE_DIR, 'uploads/settings/gsx_cert.pem')
GSX_KEY = os.path.join(BASE_DIR, 'uploads/settings/gsx_key.pem')

os.environ['GSX_CERT'] = GSX_CERT
os.environ['GSX_KEY'] = GSX_KEY

CELERYBEAT_SCHEDULE = {
    'check_mail': {
        'task': 'servo.tasks.check_mail',
        'schedule': timedelta(seconds=300),
    },
}

WKHTMLTOPDF_ENV = {
    'ignore_404': 'True'
}

WKHTMLTOPDF_CMD = '/usr/local/bin/wkhtmltopdf'
WKHTMLTOPDF_CMD_OPTIONS = {
    'quiet': True,
    'zoom': '2.5',
    'page-size': 'a4'
}

from local_settings import *

CACHES['comptia'] = {
    'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    'LOCATION': '127.0.0.1:11211',
    'TIMEOUT': 60 * 60 * 24,
    'KEY_PREFIX': 'comptia_'
}
