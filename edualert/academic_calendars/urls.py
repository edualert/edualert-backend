from django.urls import path
from .views import *

app_name = 'academic_calendars'
urlpatterns = [
    path('current-academic-year-calendar/', CurrentAcademicYearCalendar.as_view(), name='current-academic-year-calendar'),
]
