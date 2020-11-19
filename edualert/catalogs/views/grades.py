from django.utils import timezone
from methodtools import lru_cache

from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.generics import CreateAPIView, get_object_or_404, UpdateAPIView, DestroyAPIView
from rest_framework.response import Response

from edualert.catalogs.models import StudentCatalogPerSubject, SubjectGrade
from edualert.catalogs.serializers import SubjectGradeCreateSerializer, SubjectGradeUpdateSerializer, StudentCatalogPerSubjectSerializer
from edualert.catalogs.serializers.grades import SubjectGradeCreateBulkSerializer
from edualert.catalogs.utils import update_last_change_in_catalog, compute_averages
from edualert.catalogs.views.common import GradeAbsenceBulkCreateBase
from edualert.catalogs.utils import can_update_grades_or_absences
from edualert.common.constants import PUT, OPTIONS, HEAD, DELETE
from edualert.common.permissions import IsTeacher


class GradeCreate(CreateAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = SubjectGradeCreateSerializer

    @lru_cache(maxsize=None)
    def get_catalog(self):
        return get_object_or_404(
            StudentCatalogPerSubject.objects.select_related(
                'study_class'
            ).prefetch_related('absences', 'examination_grades'),
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

    def create(self, request, *args, **kwargs):
        catalog = self.get_catalog()
        if catalog.is_exempted:
            return Response({'message': _("Can't add grades for an exempted student.")},
                            status=status.HTTP_400_BAD_REQUEST)
        if catalog.is_coordination_subject:
            return Response({'message': _("Can't add grades for coordination subject.")},
                            status=status.HTTP_400_BAD_REQUEST)

        # TODO uncomment after it's tested
        # if not can_update_grades_or_absences(catalog.study_class):
        #     return Response({'message': _("Can't create grades at this time.")},
        #                     status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)


class GradeDetail(UpdateAPIView, DestroyAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = SubjectGradeUpdateSerializer
    http_method_names = [DELETE.lower(), PUT.lower(), OPTIONS.lower(), HEAD.lower()]

    @lru_cache(maxsize=None)
    def get_object(self):
        return get_object_or_404(
            SubjectGrade.objects.select_related(
                'catalog_per_subject__study_class'
            ).prefetch_related(
                'catalog_per_subject__absences', 'catalog_per_subject__examination_grades'
            ),
            id=self.kwargs['id'],
            catalog_per_subject__teacher_id=self.request.user.user_profile
        )

    def check_grade_can_be_edited(self):
        grade = self.get_object()

        # TODO uncomment after it's tested
        # if not can_update_grades_or_absences(grade.catalog_per_subject.study_class):
        #     return Response({'message': _(f'Cannot {action} grades at this time.')},
        #                     status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        return self.check_grade_can_be_edited() or super().update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        catalog = instance.catalog_per_subject

        if catalog.is_coordination_subject:
            return Response({'message': _("Can't delete coordination subject grade.")},
                            status=status.HTTP_400_BAD_REQUEST)

        error = self.check_grade_can_be_edited()
        if error:
            return error

        instance.delete()

        compute_averages([catalog], instance.semester)
        update_last_change_in_catalog(request.user.user_profile)
        return Response(StudentCatalogPerSubjectSerializer(catalog).data)


class GradesBulkCreate(GradeAbsenceBulkCreateBase):
    serializer_class = SubjectGradeCreateBulkSerializer
    cannot_update_message = _("Can't add grades at this time.")

    def post(self, request, *args, **kwargs):
        subject = self.get_subject()
        if subject.is_coordination:
            return Response({'message': _("Can't add grades for coordination subject.")},
                            status=status.HTTP_400_BAD_REQUEST)

        return super().post(request, *args, **kwargs)
