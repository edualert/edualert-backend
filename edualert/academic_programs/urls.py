from django.urls import path
from . import views

app_name = 'academic_programs'
urlpatterns = [
    path('unregistered-academic-programs/', views.UnregisteredAcademicProgramList.as_view(), name='unregistered-academic-program-list'),
    path('generic-academic-programs/', views.GenericAcademicProgramList.as_view(), name='generic-academic-program-list'),
    path('generic-academic-programs/<int:id>/', views.GenericAcademicProgramDetail.as_view(), name='generic-academic-program-detail'),
    path('academic-programs/<int:id>/', views.AcademicProgramDetail.as_view(), name='academic-program-detail'),
    path('academic-programs/<int:id>/subjects/', views.AcademicProgramSubjectList.as_view(), name='academic-program-subject-list'),
    path('years/<int:academic_year>/academic-programs/', views.AcademicProgramList.as_view(), name='academic-program-list'),
]
