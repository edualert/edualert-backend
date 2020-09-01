from .common import *
import os

ALLOWED_HOSTS = ['localhost', ]


# DJANGO DEBUG TOOLBAR
# ------------------------------------------------------------------------------
# Only show the toolbar when needed since it severely impacts performance
if os.environ.get('SHOW_TOOLBAR'):
    def show_toolbar(request):
        return True

    MIDDLEWARE += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    INSTALLED_APPS += ('debug_toolbar', )
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': '{}.show_toolbar'.format(__name__),
    }

# CUSTOM MIDDLEWARES
# ------------------------------------------------------------------------------
# This will print all database queries to stdout
# This is not compatible with django debug toolbar, since the toolbar empties the django
# connection object so this won't print anything
if not os.environ.get('SHOW_TOOLBAR'):
    MIDDLEWARE.insert(1, 'edualert.common.middleware.SQLPrintingMiddleware')

# CELERY
# ------------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES = True

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
