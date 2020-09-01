from methodtools import lru_cache
from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from edualert.catalogs.models import StudentCatalogPerSubject, ExaminationGrade
from edualert.catalogs.serializers import ExaminationGradeCreateSerializer, ExaminationGradeUpdateSerializer, StudentCatalogPerSubjectSerializer
from edualert.catalogs.utils import can_update_examination_grades, update_last_change_in_catalog, change_averages_after_examination_grade_operation
from edualert.common.constants import PUT, OPTIONS, HEAD, DELETE
from edualert.common.permissions import IsTeacher


class ExaminationGradeCreate(generics.CreateAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = ExaminationGradeCreateSerializer

    def get_catalog(self):
        return get_object_or_404(
            StudentCatalogPerSubject.objects.select_related(
                'study_class'
            ).prefetch_related('grades', 'absences'),
            id=self.kwargs['id'],
            teacher_id=self.request.user.user_profile.id,
            is_enrolled=True,
            student__is_active=True
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'catalog': self.get_catalog()
        })
        return context


class ExaminationGradeDetail(generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = ExaminationGradeUpdateSerializer
    http_method_names = [DELETE.lower(), PUT.lower(), OPTIONS.lower(), HEAD.lower()]

    @lru_cache(maxsize=None)
    def get_object(self):
        return get_object_or_404(
            ExaminationGrade.objects.select_related(
                'catalog_per_subject__study_class'
            ).prefetch_related(
                'catalog_per_subject__grades', 'catalog_per_subject__absences'
            ),
            id=self.kwargs['id'],
            catalog_per_subject__teacher_id=self.request.user.user_profile
        )

    def check_grade_can_be_edited(self):
        examination_grade = self.get_object()

        action = _('delete') if self.request.method == DELETE else _('update')
        if examination_grade.created < timezone.now() - timezone.timedelta(hours=2):
            return Response({'message': _('Cannot {} a grade that was created more than 2 hours ago.').format(action)},
                            status=status.HTTP_400_BAD_REQUEST)

        if not can_update_examination_grades(examination_grade.catalog_per_subject.study_class, examination_grade.grade_type):
            return Response({'message': _('Cannot {} grades at this time.').format(action)},
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        return self.check_grade_can_be_edited() or super().update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        error = self.check_grade_can_be_edited()
        if error:
            return error

        instance = self.get_object()
        instance.delete()

        change_averages_after_examination_grade_operation([instance.catalog_per_subject], instance.grade_type, instance.semester)
        update_last_change_in_catalog(request.user.user_profile)

        return Response(StudentCatalogPerSubjectSerializer(instance.catalog_per_subject).data)
