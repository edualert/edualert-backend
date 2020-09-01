from datetime import timedelta

from django.db.models import F
from django.db.models.functions import Lower
from django.http import Http404
from django.utils import timezone
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.common.permissions import IsAdministrator
from edualert.schools.models import RegisteredSchoolUnit
from edualert.statistics.models import SchoolUnitStats, SchoolUnitEnrollmentStats
from edualert.statistics.pagination import StatisticsPagination
from edualert.statistics.serializers import SchoolUnitStatsAverageSerializer, SchoolUnitStatsAbsencesSerializer, \
    RegisteredSchoolUnitLastChangeInCatalogSerializer, RegisteredSchoolUnitRiskSerializer


class SchoolUnitsAverages(generics.ListAPIView):
    permission_classes = (IsAdministrator,)
    pagination_class = StatisticsPagination
    serializer_class = SchoolUnitStatsAverageSerializer

    def get_queryset(self):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return SchoolUnitStats.objects.none()

        order_by = 'avg_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else 'avg_annual'

        return SchoolUnitStats.objects.filter(
            academic_year=current_calendar.academic_year
        ).order_by(
            F(order_by).desc(nulls_last=True),
            Lower('school_unit_name')
        )


class SchoolUnitsAbsences(generics.ListAPIView):
    permission_classes = (IsAdministrator,)
    pagination_class = StatisticsPagination
    serializer_class = SchoolUnitStatsAbsencesSerializer

    def get_queryset(self):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return SchoolUnitStats.objects.none()

        order_by = 'unfounded_abs_avg_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else 'unfounded_abs_avg_annual'

        return SchoolUnitStats.objects.filter(
            academic_year=current_calendar.academic_year
        ).order_by(
            F(order_by).desc(nulls_last=True),
            Lower('school_unit_name')
        )


class InactiveSchoolUnits(generics.ListAPIView):
    permission_classes = (IsAdministrator,)
    pagination_class = StatisticsPagination
    serializer_class = RegisteredSchoolUnitLastChangeInCatalogSerializer

    def get_queryset(self):
        return RegisteredSchoolUnit.objects.filter(
            last_change_in_catalog__lt=timezone.now() - timedelta(days=30)
        ).order_by(
            '-last_change_in_catalog',
            Lower('name')
        )


class SchoolUnitsAtRisk(generics.ListAPIView):
    permission_classes = (IsAdministrator,)
    pagination_class = StatisticsPagination
    serializer_class = RegisteredSchoolUnitRiskSerializer

    def get_queryset(self):
        return RegisteredSchoolUnit.objects.filter(
            students_at_risk_count__gt=0
        ).order_by(
            '-students_at_risk_count',
            Lower('name')
        )


class InstitutionsEnrollmentStats(APIView):
    permission_classes = (IsAdministrator,)

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        month = self.request.GET.get('month')
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            raise Http404()

        if month and not (month.isnumeric() and 1 <= int(month) <= 12) or not month:
            month = today.month

        enrollment_stats = get_object_or_404(
            SchoolUnitEnrollmentStats,
            year=today.year if int(month) <= today.month else current_calendar.academic_year,
            month=month
        )
        return Response(enrollment_stats.daily_statistics)
