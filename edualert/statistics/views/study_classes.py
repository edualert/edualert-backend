from django.db.models import F
from django.utils import timezone
from rest_framework import generics

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.common.permissions import IsPrincipal, IsTeacherOrPrincipal
from edualert.profiles.models import UserProfile
from edualert.statistics.pagination import StatisticsPagination
from edualert.statistics.serializers import StudyClassesAveragesSerializer, StudyClassesAbsencesSerializer, \
    StudyClassesRiskSerializer
from edualert.study_classes.models import StudyClass


class StudyClassesAverages(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    pagination_class = StatisticsPagination
    serializer_class = StudyClassesAveragesSerializer

    def get_queryset(self):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return StudyClass.objects.none()

        order_by = 'avg_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else 'avg_annual'

        return StudyClass.objects.filter(
            school_unit_id=self.request.user.user_profile.school_unit_id,
            academic_year=current_calendar.academic_year
        ).order_by(
            F(order_by).desc(nulls_last=True),
            'class_grade_arabic',
            'class_letter'
        )


class StudyClassesAbsences(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    pagination_class = StatisticsPagination
    serializer_class = StudyClassesAbsencesSerializer

    def get_queryset(self):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return StudyClass.objects.none()

        order_by = 'unfounded_abs_avg_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else 'unfounded_abs_avg_annual'

        return StudyClass.objects.filter(
            school_unit_id=self.request.user.user_profile.school_unit_id,
            academic_year=current_calendar.academic_year
        ).order_by(
            F(order_by).desc(nulls_last=True),
            'class_grade_arabic',
            'class_letter'
        )


class StudyClassesAtRisk(generics.ListAPIView):
    permission_classes = (IsTeacherOrPrincipal,)
    pagination_class = StatisticsPagination
    serializer_class = StudyClassesRiskSerializer

    def get_queryset(self):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return StudyClass.objects.none()

        profile = self.request.user.user_profile
        filters = {
            'school_unit_id': profile.school_unit_id,
            'academic_year': current_calendar.academic_year,
            'students_at_risk_count__gt': 0
        }
        if profile.user_role == UserProfile.UserRoles.TEACHER:
            filters['teachers'] = profile

        return StudyClass.objects.filter(
            **filters
        ).distinct() \
            .order_by(
            '-students_at_risk_count',
            'class_grade_arabic',
            'class_letter'
        )
