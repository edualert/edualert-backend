from django.db.models import F
from django.db.models.functions import Lower
from django.utils import timezone
from rest_framework import generics

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.academic_programs.models import AcademicProgram
from edualert.common.permissions import IsPrincipal
from edualert.statistics.pagination import StatisticsPagination
from edualert.statistics.serializers import AcademicProgramsAverageSerializer, AcademicProgramsAbsencesSerializer, \
    AcademicProgramsRiskSerializer


class AcademicProgramsAverages(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    pagination_class = StatisticsPagination
    serializer_class = AcademicProgramsAverageSerializer

    def get_queryset(self):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return AcademicProgram.objects.none()

        order_by = 'avg_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else 'avg_annual'

        return AcademicProgram.objects.filter(
            school_unit_id=self.request.user.user_profile.school_unit_id,
            academic_year=current_calendar.academic_year,
        ).order_by(
            F(order_by).desc(nulls_last=True),
            Lower('name')
        )


class AcademicProgramsAbsences(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    pagination_class = StatisticsPagination
    serializer_class = AcademicProgramsAbsencesSerializer

    def get_queryset(self):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return AcademicProgram.objects.none()

        order_by = 'unfounded_abs_avg_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else 'unfounded_abs_avg_annual'

        return AcademicProgram.objects.filter(
            school_unit_id=self.request.user.user_profile.school_unit_id,
            academic_year=current_calendar.academic_year
        ).order_by(
            F(order_by).desc(nulls_last=True),
            Lower('name')
        )


class AcademicProgramsAtRisk(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    pagination_class = StatisticsPagination
    serializer_class = AcademicProgramsRiskSerializer

    def get_queryset(self):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return AcademicProgram.objects.none()

        return AcademicProgram.objects.filter(
            school_unit_id=self.request.user.user_profile.school_unit_id,
            academic_year=current_calendar.academic_year,
            students_at_risk_count__gt=0
        ).order_by(
            '-students_at_risk_count',
            Lower('name')
        )
