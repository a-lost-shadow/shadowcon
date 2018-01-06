"""
Django settings for shadowcon project.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
DEFAULT_SECRET_KEY = "Not really secret, only for development"
SECRET_KEY = os.environ.get('SECRET_KEY', DEFAULT_SECRET_KEY)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG') == 'True'

ALLOWED_HOSTS = [
    "new.shadowcon.net",
    "www.shadowcon.net",
	"localhost",
    "shadowcon.herokuapp.com",
]


# Application definition

INSTALLED_APPS = (
    'page.apps.PageConfig',
    'ckeditor',
    'contact.apps.ContactConfig',
    'convention.apps.ConConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django_ajax',
    'reversion',
    'reversion_compare',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'shadowcon.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'shadowcon.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

localSQLiteUrl = 'sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')

db_from_env = dj_database_url.config(conn_max_age=500, default=localSQLiteUrl)
DATABASES = {
    'default': db_from_env,
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, 'static'),
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

CKEDITOR_JQUERY_URL = '//ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js'

CKEDITOR_ALLOW_NONIMAGE_FILES = False

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'stardard',
        'toolbarGroups':  [
            {'name': 'document', 'groups': [ 'mode', 'document', 'doctools' ] },
            {'name': 'clipboard', 'groups': [ 'clipboard', 'undo' ] },
            {'name': 'editing', 'groups': [ 'find', 'selection', 'spellchecker', 'editing' ] },
            {'name': 'forms', 'groups': [ 'forms' ] },
            {'name': 'insert', 'groups': [ 'insert' ] },
            {'name': 'basicstyles', 'groups': [ 'basicstyles', 'cleanup' ] },
            {'name': 'paragraph', 'groups': [ 'list', 'indent', 'blocks', 'align', 'bidi', 'paragraph' ] },
            {'name': 'links', 'groups': [ 'links' ] },
            {'name': 'styles', 'groups': [ 'styles' ] },
            {'name': 'colors', 'groups': [ 'colors' ] },
            {'name': 'tools', 'groups': [ 'tools' ] },
            {'name': 'others', 'groups': [ 'others' ] },
            {'name': 'about', 'groups': [ 'about' ] }
        ],
        'removeButtons': 'Source,Form,Checkbox,Radio,TextField,Textarea,Select,'
                         'Button,ImageButton,HiddenField,Flash,Iframe,CreateDiv,Language',
        'width': "685px",
    },
}

LOGIN_REDIRECT_URL = '/user//profile/'
LOGIN_URL = '/login/'


if 'EMAIL_USER' in os.environ and 'EMAIL_PASSWD' in os.environ:
    EMAIL_USE_TLS = True
    EMAIL_HOST = 'smtp.mailgun.org'
    EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWD')
    EMAIL_PORT = '587'
else:
    EMAIL_HOST = 'mailtrap.io'
    EMAIL_PORT = '2525'
    EMAIL_HOST_USER = 'd7ab5d07b2e713'
    EMAIL_HOST_PASSWORD = '311e614f5e104f'

DEFAULT_FROM_EMAIL = 'ShadowCon Website <postmaster@mg.shadowcon.net>'

ACCOUNT_ACTIVATION_DAYS = 7  # One-week registration activation window;
