from django.db.models import Q
from django.utils import timezone
from methodtools import lru_cache

from django.utils.translation import gettext as _
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from edualert.catalogs.models import StudentCatalogPerSubject, SubjectAbsence
from edualert.catalogs.serializers import SubjectAbsenceCreateSerializer, StudentCatalogPerSubjectSerializer, \
    SubjectAbsenceCreateBulkSerializer
from edualert.catalogs.utils import can_update_grades_or_absences, update_last_change_in_catalog, \
    change_absences_counts_on_authorize, change_absences_counts_on_delete
from edualert.catalogs.views.common import GradeAbsenceBulkCreateBase
from edualert.common.permissions import IsTeacher


class AbsenceCreate(generics.CreateAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = SubjectAbsenceCreateSerializer

    @lru_cache(maxsize=None)
    def get_object(self):
        return get_object_or_404(
            StudentCatalogPerSubject.objects.select_related('study_class')
                .prefetch_related('grades', 'examination_grades'),
            id=self.kwargs['id'],
            student__is_active=True,
            teacher_id=self.request.user.user_profile.id,
            is_enrolled=True
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'catalog': self.get_object()})
        return context

    def post(self, request, *args, **kwargs):
        catalog = self.get_object()
        # TODO uncomment after it's tested
        # if not can_update_grades_or_absences(catalog.study_class):
        #     return Response({'message': _("Can't add absences at this time.")}, status=status.HTTP_400_BAD_REQUEST)

        return self.create(request, *args, **kwargs)


class AbsenceAuthorize(generics.GenericAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = StudentCatalogPerSubjectSerializer

    def get_object(self):
        profile = self.request.user.user_profile
        return get_object_or_404(
            SubjectAbsence.objects.select_related('catalog_per_subject__study_class')
                .prefetch_related('catalog_per_subject__grades', 'catalog_per_subject__examination_grades')
                .filter(Q(catalog_per_subject__teacher_id=profile.id) |
                        Q(catalog_per_subject__study_class__class_master_id=profile.id)),
            id=self.kwargs['id']
        )

    def post(self, request, *args, **kwargs):
        absence = self.get_object()
        catalog = absence.catalog_per_subject

        if absence.is_founded:
            return Response({'message': _("This absence is already authorized.")}, status=status.HTTP_400_BAD_REQUEST)

        # TODO uncomment after it's tested
        # if not can_update_grades_or_absences(catalog.study_class):
        #     return Response({'message': _("Can't authorize absences at this time.")}, status=status.HTTP_400_BAD_REQUEST)

        absence.is_founded = True
        absence.save()
        change_absences_counts_on_authorize(catalog, absence)
        update_last_change_in_catalog(self.request.user.user_profile)

        serializer = self.get_serializer(instance=catalog)
        return Response(serializer.data)


class AbsenceDelete(generics.DestroyAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = StudentCatalogPerSubjectSerializer

    def get_object(self):
        profile = self.request.user.user_profile
        return get_object_or_404(
            SubjectAbsence.objects.select_related('catalog_per_subject__study_class')
                .prefetch_related('catalog_per_subject__grades', 'catalog_per_subject__examination_grades')
                .filter(catalog_per_subject__teacher_id=profile.id),
            id=self.kwargs['id']
        )

    def delete(self, request, *args, **kwargs):
        absence = self.get_object()
        catalog = absence.catalog_per_subject

        # TODO uncomment after it's tested
        # if not can_update_grades_or_absences(catalog.study_class):
        #     return Response({'message': _("Can't delete absences at this time.")}, status=status.HTTP_400_BAD_REQUEST)

        if absence.created < timezone.now() - timezone.timedelta(days=7):
            return Response({'message': _("You can't delete this absence anymore.")}, status=status.HTTP_400_BAD_REQUEST)

        semester = absence.semester
        is_founded = absence.is_founded

        absence.delete()
        change_absences_counts_on_delete(catalog, semester, is_founded)
        update_last_change_in_catalog(self.request.user.user_profile)

        serializer = self.get_serializer(instance=catalog)
        return Response(serializer.data)


class AbsenceBulkCreate(GradeAbsenceBulkCreateBase):
    serializer_class = SubjectAbsenceCreateBulkSerializer
    cannot_update_message = _("Can't add absences at this time.")
