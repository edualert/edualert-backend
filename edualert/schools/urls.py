from django.urls import path
from . import views

app_name = 'schools'
urlpatterns = [
    path('districts/', views.DistrictList.as_view(), name='district-list'),
    path('cities/<str:district>/', views.CityByDistrictList.as_view(), name='city-by-district-list'),
    path('school-units/', views.SchoolUnitList.as_view(), name='school-unit-list'),
    path('school-units/<int:id>/', views.SchoolUnitDetail.as_view(), name='school-unit-detail'),
    path('school-units/<int:id>/activate/', views.SchoolUnitActivate.as_view(), name='school-unit-activate'),
    path('school-units/<int:id>/deactivate/', views.SchoolUnitDeactivate.as_view(), name='school-unit-deactivate'),
    path('school-units-categories/', views.SchoolUnitCategoryList.as_view(), name='school-unit-category-list'),
    path('school-units-profiles/', views.SchoolUnitProfileList.as_view(), name='school-unit-profile-list'),
    path('school-units-names/', views.SchoolUnitNameList.as_view(), name='school-unit-name-list'),
    path('unregistered-school-units/', views.UnregisteredSchoolUnitList.as_view(), name='unregistered-school-unit-list'),
    path('my-school-unit/', views.MySchoolUnit.as_view(), name='my-school-unit'),
]
