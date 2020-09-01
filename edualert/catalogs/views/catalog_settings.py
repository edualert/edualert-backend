from django.db.models.functions import Lower
from methodtools import lru_cache
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from edualert.catalogs.serializers import CatalogSettingsSerializer
from edualert.catalogs.utils import update_last_change_in_catalog
from edualert.common.permissions import IsTeacher
from edualert.study_classes.models import StudyClass
from edualert.subjects.models import Subject


class CatalogSettings(generics.ListAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = CatalogSettingsSerializer
    pagination_class = None

    @lru_cache(maxsize=None)
    def get_subject(self):
        return get_object_or_404(Subject, id=self.kwargs['subject_id'])

    @lru_cache(maxsize=None)
    def get_study_class(self):
        return get_object_or_404(
            StudyClass.objects.select_related('academic_program').distinct(),
            id=self.kwargs['study_class_id'],
            teachers=self.request.user.user_profile,
            teacher_class_through__subject_id=self.get_subject().id
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'subject': self.get_subject(),
            'study_class': self.get_study_class(),
        })
        return context

    def get_queryset(self):
        return self.get_study_class().student_catalogs_per_subject.filter(
            subject_id=self.get_subject().id,
            teacher_id=self.request.user.user_profile.id,
            student__is_active=True,
        ).select_related('student', 'subject') \
            .order_by(Lower('student__full_name'))

    def put(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        update_last_change_in_catalog(self.request.user.user_profile)

        return Response(serializer.data)
