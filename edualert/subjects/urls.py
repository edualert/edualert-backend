from django.urls import path
from . import views

app_name = 'subjects'
urlpatterns = [
    path('subjects/', views.SubjectList.as_view(), name='subject-list'),
]
