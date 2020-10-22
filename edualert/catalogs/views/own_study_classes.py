from django.db.models import Count, Max
from django.db.models.functions import Lower
from django.http import Http404
from methodtools import lru_cache
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.serializers import StudentCatalogPerYearSerializer, PupilStudyClassSerializer, StudentCatalogPerSubjectSerializer
from edualert.catalogs.utils import get_avg_limit_for_subject, has_technological_category, get_working_weeks_count, get_weekly_hours_count
from edualert.common.permissions import IsTeacher
from edualert.common.search_and_filters import CommonOrderingFilter
from edualert.profiles.models import UserProfile
from edualert.study_classes.models import StudyClass
from edualert.subjects.models import Subject


class OwnStudyClassPupilList(generics.ListAPIView):
    permission_classes = (IsTeacher,)
    filter_backends = [CommonOrderingFilter]
    ordering_fields = [
        'student_name', 'avg_sem1', 'avg_sem2', 'avg_final',
        'abs_count_sem1', 'abs_count_sem2', 'abs_count_annual'
    ]
    ordering = ['student_name']
    ordering_extra_annotations = {'student_name': Lower('student__full_name')}
    serializer_class = StudentCatalogPerYearSerializer
    pagination_class = None

    def get_queryset(self):
        study_class = get_object_or_404(
            StudyClass,
            id=self.kwargs['id'],
            class_master=self.request.user.user_profile
        )
        return study_class.student_catalogs_per_year.filter(student__is_active=True) \
            .select_related('student').prefetch_related('student__labels')


class OwnStudyClassPupilDetail(generics.RetrieveAPIView):
    permission_classes = (IsTeacher,)
    serializer_class = PupilStudyClassSerializer

    @lru_cache(maxsize=None)
    def get_study_class(self):
        return get_object_or_404(
            StudyClass,
            id=self.kwargs['study_class_id'],
            class_master=self.request.user.user_profile
        )

    def get_object(self):
        profile = get_object_or_404(
            UserProfile,
            id=self.kwargs['pupil_id'],
            is_active=True
        )
        if not profile.student_catalogs_per_year.filter(study_class_id=self.get_study_class().id).exists():
            raise Http404()
        return profile

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'study_class': self.get_study_class()
        })
        return context


class OwnStudyClassCatalogBySubject(generics.ListAPIView):
    permission_classes = (IsTeacher,)
    filter_backends = [CommonOrderingFilter]
    ordering_fields = [
        'student_name', 'avg_sem1', 'avg_sem2', 'avg_final',
        'abs_count_sem1', 'abs_count_sem2', 'abs_count_annual',
        'grades_count', 'last_grade_date'
    ]
    ordering = ['student_name']
    ordering_extra_annotations = {
        'student_name': Lower('student__full_name'),
        'grades_count': Count('grade'),
        'last_grade_date': Max('grade__taken_at')
    }
    serializer_class = StudentCatalogPerSubjectSerializer
    pagination_class = None

    @lru_cache(maxsize=None)
    def get_subject(self):
        return get_object_or_404(Subject, id=self.kwargs['subject_id'])

    @lru_cache(maxsize=None)
    def get_study_class(self):
        profile = self.request.user.user_profile
        subject = self.get_subject()
        return get_object_or_404(
            StudyClass.objects.distinct(),
            id=self.kwargs['study_class_id'],
            teachers=profile,
            teacher_class_through__subject_id=subject.id
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        study_class = self.get_study_class()
        subject = self.get_subject()
        calendar = get_current_academic_calendar()

        is_technological_school = has_technological_category(study_class.school_unit)
        working_weeks_count_sem1 = get_working_weeks_count(calendar, 1, study_class, is_technological_school)
        working_weeks_count_sem2 = get_working_weeks_count(calendar, 2, study_class, is_technological_school)
        weekly_hours_count = get_weekly_hours_count(study_class, subject.id)

        third_of_hours_count_sem1 = (working_weeks_count_sem1 * weekly_hours_count) // 3
        third_of_hours_count_sem2 = (working_weeks_count_sem2 * weekly_hours_count) // 3

        context.update({
            'avg_limit': get_avg_limit_for_subject(study_class, subject.is_coordination, subject.id),
            'third_of_hours_count_sem1': third_of_hours_count_sem1,
            'third_of_hours_count_sem2': third_of_hours_count_sem2,
            'third_of_hours_count_annual': third_of_hours_count_sem1 + third_of_hours_count_sem2,
        })
        return context

    def get_queryset(self):
        profile = self.request.user.user_profile
        subject = self.get_subject()
        study_class = self.get_study_class()

        return study_class.student_catalogs_per_subject.filter(
            subject_id=subject.id,
            teacher_id=profile.id,
            is_enrolled=True,
            student__is_active=True
        ).select_related('student').prefetch_related('grades', 'absences', 'examination_grades', 'student__labels')
