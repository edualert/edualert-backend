from rest_framework import generics

from edualert.catalogs.models import StudentCatalogPerSubject, StudentCatalogPerYear
from edualert.catalogs.serializers.catalogs_per_subject import CatalogsPerSubjectRemarksSerializer
from edualert.common.constants import GET, PUT, OPTIONS, HEAD
from edualert.catalogs.serializers.catalogs_per_year import CatalogsPerYearRemarksSerializer
from edualert.common.permissions import IsTeacher


class CatalogsPerSubjectRemarks(generics.RetrieveUpdateAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = CatalogsPerSubjectRemarksSerializer
    lookup_field = 'id'
    http_method_names = [GET.lower(), PUT.lower(), OPTIONS.lower(), HEAD.lower()]

    def get_queryset(self):
        profile = self.request.user.user_profile
        return StudentCatalogPerSubject.objects.filter(
            teacher_id=profile.id,
        )


class CatalogsPerYearRemarks(generics.RetrieveUpdateAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = CatalogsPerYearRemarksSerializer
    lookup_field = 'id'
    http_method_names = [GET.lower(), PUT.lower(), OPTIONS.lower(), HEAD.lower()]

    def get_queryset(self):
        profile = self.request.user.user_profile
        return StudentCatalogPerYear.objects.filter(
            study_class__class_master_id=profile.id
        )
