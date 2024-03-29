"""
Django settings for main project.

Generated by 'django-admin startproject' using Django 4.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_SECRET_KEY=str,
    DJANGO_TIME_ZONE=(str, 'UTC'),
    DJANGO_APP_TYPE=str,  # web/worker  TODO: Use this in sentry
    DJANGO_APP_ENVIRONMENT=str,  # dev/prod
    # App Domain
    APP_DOMAIN=str,  # api.example.com
    APP_HTTP_PROTOCOL=str,  # http|https
    APP_FRONTEND_HOST=str,  # http://frontend.example.com
    DJANGO_ALLOWED_HOSTS=(list, ['*']),
    SESSION_COOKIE_DOMAIN=str,
    CSRF_COOKIE_DOMAIN=str,
    # Database
    DB_NAME=str,
    DB_USER=str,
    DB_PASSWORD=str,
    DB_HOST=str,
    DB_PORT=(int, 5432),
    # Celery
    CELERY_BROKER_URL=str,
    # Cache
    CACHE_REDIS_URL=str,
    # Email
    EMAIL_HOST=str,
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=str,
    EMAIL_HOST_PASSWORD=str,
    DEFAULT_FROM_EMAIL=str,
    # Misc
)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DJANGO_DEBUG')

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS')

APP_SITE_NAME = 'Alert-Hub'
APP_HTTP_PROTOCOL = env('APP_HTTP_PROTOCOL')
APP_DOMAIN = env('APP_DOMAIN')
APP_FRONTEND_HOST = env('APP_FRONTEND_HOST')

DJANGO_APP_ENVIRONMENT = env('DJANGO_APP_ENVIRONMENT')


# Application definition
INSTALLED_APPS = [
    # Native
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # External
    'strawberry_django',
    'django_celery_beat',
    'django_extensions',
    'corsheaders',
    'storages',
    # Internal
    'apps.common',
    'apps.user',
    'apps.cap_feed',
    'apps.subscription',
    'apps.subscription_manager',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


ROOT_URLCONF = 'main.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'main.wsgi.application'

# Security

# Security Header configuration
SESSION_COOKIE_NAME = f'alert-hub-{DJANGO_APP_ENVIRONMENT}-sessionid'
CSRF_COOKIE_NAME = f'alert-hub-{DJANGO_APP_ENVIRONMENT}-csrftoken'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSP_DEFAULT_SRC = ["'self'"]
SECURE_REFERRER_POLICY = 'same-origin'
if APP_HTTP_PROTOCOL == 'https':
    SESSION_COOKIE_NAME = f'__Secure-{SESSION_COOKIE_NAME}'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 30  # TODO: Increase this slowly
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    CSRF_TRUSTED_ORIGINS = [
        APP_FRONTEND_HOST,
        f'{APP_HTTP_PROTOCOL}://{APP_DOMAIN}',
    ]

# -- https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-SESSION_COOKIE_DOMAIN
SESSION_COOKIE_DOMAIN = env('SESSION_COOKIE_DOMAIN')
# https://docs.djangoproject.com/en/3.2/ref/settings/#csrf-cookie-domain
CSRF_COOKIE_DOMAIN = env('CSRF_COOKIE_DOMAIN')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'user.User'

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('DJANGO_TIME_ZONE')
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/
# TODO: Use custom config for static files
STATICFILES_DIRS = (str(BASE_DIR.joinpath('static')),)
STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CELERY
CELERY_RESULT_BACKEND = CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# CORS
CORS_ORIGIN_ALLOW_ALL = True  # TODO: Use whitelist instead
CORS_ALLOW_CREDENTIALS = True
CORS_URLS_REGEX = r'(^/media/.*$)|(^/graphql/$)'
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
)

CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'sentry-trace',
)

# Graphql
STRAWBERRY_ENUM_TO_STRAWBERRY_ENUM_MAP = 'main.graphql.enums.ENUM_TO_STRAWBERRY_ENUM_MAP'
STRAWBERRY_DEFAULT_PAGINATION_LIMIT = 50
STRAWBERRY_MAX_PAGINATION_LIMIT = 100

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('CACHE_REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}

# Email - SMTP Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# TODO: Add logging for PROD
if DEBUG:

    def log_render_extra_context(record):
        '''
        Append extra->context to logs
        NOTE: This will appear in logs when used with logger.xxx(..., extra={'context': {..content}})
        '''
        if hasattr(record, 'context'):
            record.context = f' - {str(record.context)}'
        else:
            record.context = ''
        return True

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'render_extra_context': {
                '()': 'django.utils.log.CallbackFilter',
                'callback': log_render_extra_context,
            }
        },
        'formatters': {
            'colored_verbose': {
                '()': 'colorlog.ColoredFormatter',
                'format': (
                    "%(log_color)s%(levelname)-8s%(red)s%(module)-8s%(reset)s %(asctime)s %(blue)s%(message)s %(context)s"
                ),
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'filters': ['render_extra_context'],
            },
            'colored_console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'colored_verbose',
                'filters': ['render_extra_context'],
            },
        },
        'loggers': {
            **{
                app: {
                    'handlers': ['colored_console'],
                    'level': 'INFO',
                    'propagate': True,
                }
                for app in ['apps', 'helix', 'utils', 'celery', 'django']
            },
            'profiling': {
                'handlers': ['colored_console'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }
