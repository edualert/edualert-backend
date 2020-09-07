from .common import *

SECRET_KEY = env('DJANGO_SECRET_KEY')

ADMINS = [
    ('Madalina Gal', 'madalina.gal@rodeapps.com'),
    ('Vlad Tura', 'vlad.tura@rodeapps.com'),
]


# CACHE CONFIG
# ------------------------------------------------------------------------------
CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env('CACHE_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': None
        }
}


# STORAGE
# ------------------------------------------------------------------------------
# DATABASE_URL must be given as an environment variable or as a secret, else this will fail
DATABASES = {
    'default': env.db_url_config(env(DATABASE_URL_KEY))
}
DATABASES['default']['CONN_MAX_AGE'] = 500

# EMAILS
# ------------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_CONFIG = env.email_url('EMAIL_URL')
vars().update(EMAIL_CONFIG)
