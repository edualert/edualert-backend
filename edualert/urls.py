"""edualert URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from .common import urls as common_urls
from .profiles import urls as profile_urls
from .schools import urls as school_urls
from .subjects import urls as subject_urls
from .academic_calendars import urls as academic_calendars_urls
from .academic_programs import urls as academic_programs_urls
from .study_classes import urls as study_classes_urls
from .notifications import urls as notifications_urls
from .catalogs import urls as catalogs_urls
from .statistics import urls as statistics_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oauth2/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('api/v1/', include(common_urls, namespace='common')),
    path('api/v1/', include(profile_urls, namespace='users')),
    path('api/v1/', include(school_urls, namespace='schools')),
    path('api/v1/', include(subject_urls, namespace='subjects')),
    path('api/v1/', include(academic_calendars_urls, namespace='academic_calendars')),
    path('api/v1/', include(academic_programs_urls, namespace='academic_programs')),
    path('api/v1/', include(study_classes_urls, namespace='study_classes')),
    path('api/v1/', include(notifications_urls, namespace='notifications')),
    path('api/v1/', include(catalogs_urls, namespace='catalogs')),
    path('api/v1/', include(statistics_urls, namespace='statistics')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
