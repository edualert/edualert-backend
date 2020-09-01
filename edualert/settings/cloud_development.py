from .cloud_common import *

DEBUG = True

# CORS
CORS_ORIGIN_ALLOW_ALL = True

# Throttling
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = (
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
)

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/minute',
    'user': '300/minute',
    'password-views': '10/minute',
}

DATABASES['default']['CONN_MAX_AGE'] = 500


ALLOWED_HOSTS = ['*']

# BROWSABLE API
# ------------------------------------------------------------------------------
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += ('rest_framework.renderers.BrowsableAPIRenderer',)
