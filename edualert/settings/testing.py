from .common import *

import logging

# LOGGING
# ------------------------------------------------------------------------------
# Suppress the amount of logging that FactoryBoy outputs
logging.getLogger("factory").setLevel(logging.WARN)
# Disable request logging that is not CRITICAL
logging.disable(logging.CRITICAL)


# ENVIRONMENT
# ------------------------------------------------------------------------------
ENVIRONMENT = 'TESTING'

# PASSWORD HASHING
# ------------------------------------------------------------------------------
# MD5 is fast, perfect for testing.
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# CELERY
# ------------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES = True

# EMAILS
# ------------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
