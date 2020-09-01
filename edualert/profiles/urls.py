from django.urls import path
from . import views

app_name = 'users'
urlpatterns = [
    path('users/', views.UserProfileList.as_view(), name='user-profile-list'),
    path('users/<int:id>/', views.UserProfileDetail.as_view(), name='user-profile-detail'),
    path('users/<int:id>/activate/', views.UserProfileActivate.as_view(), name='user-profile-activate'),
    path('users/<int:id>/deactivate/', views.UserProfileDeactivate.as_view(), name='user-profile-deactivate'),

    path('labels/', views.LabelList.as_view(), name='label-list'),

    path('school-principals/', views.SchoolPrincipalList.as_view(), name='school-principal-list'),
    path('parents/', views.ParentList.as_view(), name='parent-list'),
    path('teachers/', views.TeacherList.as_view(), name='teacher-list'),
    path('students/', views.StudentList.as_view(), name='student-list'),
    path('my-account/', views.MyAccountDetail.as_view(), name='my-account'),

    path('forgot-password/', views.ForgotPassword.as_view(), name='forgot-password'),
    path('set-password/<slug:access_key>/', views.SetPassword.as_view(), name='set-password'),

    path('import-users/', views.ImportProfiles.as_view(), name='import-users'),
]
