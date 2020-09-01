from django.urls import path
from . import views

app_name = 'study_classes'
urlpatterns = [
    path('years/<int:academic_year>/study-classes-names/', views.StudyClassNameList.as_view(), name='study-class-name-list'),
    path('years/<int:academic_year>/study-classes/', views.StudyClassList.as_view(), name='study-class-list'),
    path('study-classes/<int:id>/', views.StudyClassDetail.as_view(), name='study-class-detail'),
    path('study-classes/<int:id>/cloned-to-next-year/', views.StudyClassClonedToNextYear.as_view(), name='study-class-cloned-to-next-year'),
    path('study-classes/<int:id>/receivers-counts/', views.StudyClassReceiverCounts.as_view(), name='study-class-receiver-counts'),
    path('years/<int:academic_year>/own-study-classes/', views.OwnStudyClassList.as_view(), name='own-study-class-list'),
    path('own-study-classes/<int:id>/', views.OwnStudyClassDetail.as_view(), name='own-study-class-detail'),
    path('students/<int:student_id>/study-classes/<int:study_class_id>/differences/', views.DifferenceSubjectList.as_view(), name='difference-subject-list'),
    path('students/<int:id>/move-to-study-classes/', views.MoveStudentPossibleStudyClasses.as_view(), name='move-student-possible-study-classes'),
    path('students/<int:student_id>/study-classes/<int:study_class_id>/move/', views.MoveStudent.as_view(), name='move-student'),
]
