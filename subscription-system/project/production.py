import os

from .settings import *
from .settings import BASE_DIR

# Configure the domain name using the environment variable
# that Azure automatically creates for us.
ALLOWED_HOSTS = [os.environ['WEBSITE_HOSTNAME']] if 'WEBSITE_HOSTNAME' in os.environ else []
CSRF_TRUSTED_ORIGINS = ['https://' + os.environ['WEBSITE_HOSTNAME']] if 'WEBSITE_HOSTNAME' in os.environ else []
DEBUG = False
# WhiteNoise configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'user_dir.middleware.SessionMiddleware',
    'user_dir.middleware.DeleteJWTMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'user_dir.middleware.AuthenticationMiddleware',
    'user_dir.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configure Postgres database based on connection string of the libpq Keyword/Value form
# https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
subscription_conn_str = os.environ['SUBSCRIPTION_POSTGRESQL_CONNECTIONSTRING']
subscription_conn_str_params = {pair.split('=')[0]: pair.split('=')[1] for pair in subscription_conn_str.split(' ')}
alert_conn_str = os.environ['ALERT_POSTGRESQL_CONNECTIONSTRING']
alert_conn_str_params = {pair.split('=')[0]: pair.split('=')[1] for pair in alert_conn_str.split(' ')}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': subscription_conn_str_params['dbname'],
        'HOST': subscription_conn_str_params['host'],
        'USER': subscription_conn_str_params['user'],
        'PASSWORD': subscription_conn_str_params['password'],
    },
    'AlertDB': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': alert_conn_str_params['dbname'],
        'HOST': alert_conn_str_params['host'],
        'USER': alert_conn_str_params['user'],
        'PASSWORD': alert_conn_str_params['password'],
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get("REDIS_URL"),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

DATABASE_ROUTERS = ['DBRouter.AlertDBRouter']
if "Test_Environment" in os.environ and os.environ["Test_Environment"] == 'True':
    DATABASE_ROUTERS = ['TestDBRouter.TestDBRouter']

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


