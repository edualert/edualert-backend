from django.urls import path
from . import views

app_name = 'catalogs'
urlpatterns = [
    # Own study class catalogs
    path('own-study-classes/<int:id>/pupils/', views.OwnStudyClassPupilList.as_view(), name='own-study-class-pupil-list'),
    path('own-study-classes/<int:study_class_id>/pupils/<int:pupil_id>/', views.OwnStudyClassPupilDetail.as_view(), name='own-study-class-pupil-detail'),
    path('own-study-classes/<int:study_class_id>/subjects/<int:subject_id>/catalogs/', views.OwnStudyClassCatalogBySubject.as_view(), name='own-study-class-catalog-by-subject'),
    path('own-study-classes/<int:study_class_id>/subjects/<int:subject_id>/settings/', views.CatalogSettings.as_view(), name='catalog-settings'),

    # Remarks
    path('catalogs-per-subject/<int:id>/remarks/', views.CatalogsPerSubjectRemarks.as_view(), name='catalog-per-subject-remarks'),
    path('catalogs-per-year/<int:id>/remarks/', views.CatalogsPerYearRemarks.as_view(), name='catalog-per-year-remarks'),

    # Grades
    path('catalogs/<int:id>/grades/', views.GradeCreate.as_view(), name='grade-create'),
    path('grades/<int:id>/', views.GradeDetail.as_view(), name='grade-detail'),
    path('own-study-classes/<int:study_class_id>/subjects/<int:subject_id>/bulk-grades/', views.GradesBulkCreate.as_view(), name='add-grades-in-bulk'),

    # Absences
    path('catalogs/<int:id>/absences/', views.AbsenceCreate.as_view(), name='add-absence'),
    path('absences/<int:id>/', views.AbsenceDelete.as_view(), name='delete-absence'),
    path('absences/<int:id>/authorize/', views.AbsenceAuthorize.as_view(), name='authorize-absence'),
    path('own-study-classes/<int:study_class_id>/subjects/<int:subject_id>/bulk-absences/', views.AbsenceBulkCreate.as_view(), name='add-absences-in-bulk'),

    # Examination grades
    path('catalogs/<int:id>/examination-grades/', views.ExaminationGradeCreate.as_view(), name='examination-grade-create'),
    path('examination-grades/<int:id>/', views.ExaminationGradeDetail.as_view(), name='examination-grade-detail'),

    # Export / import
    path('own-study-classes/<int:study_class_id>/subjects/<int:subject_id>/export/', views.ExportSubjectCatalogs.as_view(), name='export-subject-catalogs'),
    path('own-study-classes/<int:study_class_id>/subjects/<int:subject_id>/import/', views.ImportSubjectCatalogs.as_view(), name='import-subject-catalogs')
]
