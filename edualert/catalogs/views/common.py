from methodtools import lru_cache

from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from edualert.catalogs.serializers import SubjectAbsenceCreateBulkSerializer
from edualert.catalogs.utils import can_update_grades_or_absences
from edualert.common.permissions import IsTeacher
from edualert.study_classes.models import StudyClass
from edualert.subjects.models import Subject


class GradeAbsenceBulkCreateBase(generics.CreateAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = SubjectAbsenceCreateBulkSerializer
    cannot_update_message = None

    @lru_cache(maxsize=None)
    def get_subject(self):
        return get_object_or_404(Subject, id=self.kwargs['subject_id'])

    @lru_cache(maxsize=None)
    def get_study_class(self):
        return get_object_or_404(
            StudyClass.objects.select_related('school_unit').distinct(),
            id=self.kwargs['study_class_id'],
            teachers=self.request.user.user_profile,
            teacher_class_through__subject_id=self.get_subject().id
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'study_class': self.get_study_class(),
            'subject': self.get_subject()
        })
        return context

    def post(self, request, *args, **kwargs):
        study_class = self.get_study_class()
        # TODO uncomment after it's tested
        # if not can_update_grades_or_absences(study_class):
        #     return Response({'message': self.cannot_update_message}, status=status.HTTP_400_BAD_REQUEST)

        return self.create(request, *args, **kwargs)
