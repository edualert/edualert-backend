import calendar

from django.db.models.functions import Lower
from django.utils import timezone
from methodtools import lru_cache
from django.http import Http404
from rest_framework import generics, views
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import StudentCatalogPerSubject, StudentCatalogPerYear
from edualert.catalogs.utils import has_technological_category, get_working_weeks_count
from edualert.common.constants import WEEKDAYS_MAP
from edualert.common.permissions import IsParent, IsStudent
from edualert.profiles.models import UserProfile
from edualert.statistics.serializers import SchoolSituationSerializer, StudentStatisticsSerializer, StudentSubjectsAtRiskSerializer


class OwnChildSchoolSituation(generics.RetrieveAPIView):
    permission_classes = (IsParent,)
    serializer_class = SchoolSituationSerializer

    def get_object(self):
        parent = self.request.user.user_profile
        return get_object_or_404(
            UserProfile,
            id=self.kwargs['id'],
            user_role=UserProfile.UserRoles.STUDENT,
            parents__id=parent.id,
            school_unit_id=parent.school_unit_id
        )


class OwnSchoolSituation(generics.RetrieveAPIView):
    permission_classes = (IsStudent,)
    serializer_class = SchoolSituationSerializer

    def get_object(self):
        return self.request.user.user_profile


class OwnChildStatistics(generics.RetrieveAPIView):
    permission_classes = (IsParent,)
    serializer_class = StudentStatisticsSerializer

    def get_object(self):
        parent = self.request.user.user_profile
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            raise Http404()

        return get_object_or_404(
            StudentCatalogPerYear,
            student__id=self.kwargs['id'],
            student__parents__id=parent.id,
            student__school_unit_id=parent.school_unit_id,
            academic_year=current_calendar.academic_year
        )


class OwnStatistics(generics.RetrieveAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentStatisticsSerializer

    def get_object(self):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            raise Http404()

        return get_object_or_404(
            StudentCatalogPerYear,
            student__id=self.request.user.user_profile.id,
            academic_year=current_calendar.academic_year
        )


class OwnChildSubjectsAtRisk(generics.ListAPIView):
    permission_classes = (IsParent,)
    serializer_class = StudentSubjectsAtRiskSerializer

    @lru_cache(maxsize=None)
    def get_child(self):
        parent = self.request.user.user_profile

        return get_object_or_404(
            UserProfile.objects.select_related('student_in_class', 'school_unit'),
            id=self.kwargs['id'],
            user_role=UserProfile.UserRoles.STUDENT,
            parents__id=parent.id,
            school_unit_id=parent.school_unit_id
        )

    @lru_cache(maxsize=None)
    def get_calendar(self):
        return get_current_academic_calendar()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        child = self.get_child()
        if not child.student_in_class:
            return context

        current_calendar = self.get_calendar()
        is_technological_school = has_technological_category(child.school_unit)

        context.update({
            'working_weeks_count_sem1': get_working_weeks_count(current_calendar, 1, child.student_in_class, is_technological_school),
            'working_weeks_count_sem2': get_working_weeks_count(current_calendar, 2, child.student_in_class, is_technological_school),
        })
        return context

    def get_queryset(self):
        child = self.get_child()

        current_calendar = self.get_calendar()
        if not current_calendar:
            return StudentCatalogPerSubject.objects.none()

        order_by1 = '-unfounded_abs_count_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else '-unfounded_abs_count_annual'
        order_by2 = '-avg_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else '-avg_final'

        return child.student_catalogs_per_subject \
            .select_related('study_class__school_unit__academic_profile', 'study_class__academic_program') \
            .filter(academic_year=current_calendar.academic_year, is_at_risk=True, is_enrolled=True) \
            .order_by(order_by1, order_by2, Lower('subject_name'))


class OwnSubjectsAtRisk(generics.ListAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentSubjectsAtRiskSerializer

    @lru_cache(maxsize=None)
    def get_calendar(self):
        return get_current_academic_calendar()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        profile = self.request.user.user_profile
        if not profile.student_in_class:
            return context

        current_calendar = self.get_calendar()
        is_technological_school = has_technological_category(profile.school_unit)

        context.update({
            'working_weeks_count_sem1': get_working_weeks_count(current_calendar, 1, profile.student_in_class, is_technological_school),
            'working_weeks_count_sem2': get_working_weeks_count(current_calendar, 2, profile.student_in_class, is_technological_school),
        })
        return context

    def get_queryset(self):
        profile = self.request.user.user_profile

        current_calendar = self.get_calendar()
        if not current_calendar:
            return StudentCatalogPerSubject.objects.none()

        order_by1 = '-unfounded_abs_count_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else '-unfounded_abs_count_annual'
        order_by2 = '-avg_sem1' if timezone.now().date() < current_calendar.second_semester.ends_at else '-avg_final'

        return profile.student_catalogs_per_subject \
            .select_related('study_class__school_unit__academic_profile', 'study_class__academic_program') \
            .filter(academic_year=current_calendar.academic_year, is_at_risk=True, is_enrolled=True) \
            .order_by(order_by1, order_by2, Lower('subject_name'))


class AbsencesEvolutionBaseView(views.APIView):
    def get_month_parameter(self):
        month = self.request.query_params.get('month')
        if month is None:
            return

        try:
            month = int(month)
            if not 1 <= month <= 12:
                return
        except ValueError:
            return

        return month

    @staticmethod
    def map_absences_count_to_month_days(absences, last_day_of_month):
        absences_map = {}
        for day in range(1, last_day_of_month + 1):
            absences_map[day] = {
                'founded_count': 0,
                'unfounded_count': 0
            }

        for absence in absences:
            month_day = absence.taken_at.day
            if absence.is_founded:
                absences_map[month_day]['founded_count'] += 1
            else:
                absences_map[month_day]['unfounded_count'] += 1

        return absences_map

    def get_absences_report_for_student(self, student):
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            return []

        now = timezone.now()
        month = self.get_month_parameter() or now.month
        if month < current_calendar.first_semester.starts_at.month:
            year = now.year
        else:
            year = current_calendar.academic_year

        absences = student.absences.filter(taken_at__year=year, taken_at__month=month,
                                           created__lt=now - timezone.timedelta(hours=2))

        month_range = calendar.monthrange(year, month)
        weekday = month_range[0]
        last_day_of_month = month_range[1]
        absences_map_by_month_days = self.map_absences_count_to_month_days(absences, last_day_of_month)
        filter_by_category = True if self.request.query_params.get('by_category') == 'true' else False

        results = []
        for day in range(1, last_day_of_month + 1):
            result = {
                'day': day,
                'weekday': WEEKDAYS_MAP[weekday % 7],
            }
            if filter_by_category:
                result['founded_count'] = absences_map_by_month_days[day]['founded_count']
                result['unfounded_count'] = absences_map_by_month_days[day]['unfounded_count']
            else:
                result['total_count'] = absences_map_by_month_days[day]['founded_count'] + \
                                        absences_map_by_month_days[day]['unfounded_count']

            results.append(result)
            weekday += 1

        return results


class OwnChildAbsencesEvolution(AbsencesEvolutionBaseView):
    permission_classes = (IsParent,)

    def get_child(self):
        parent = self.request.user.user_profile

        return get_object_or_404(
            UserProfile.objects.select_related('student_in_class', 'school_unit'),
            id=self.kwargs['id'],
            user_role=UserProfile.UserRoles.STUDENT,
            parents__id=parent.id,
            school_unit_id=parent.school_unit_id
        )

    def get(self, request, *args, **kwargs):
        student = self.get_child()
        return Response(self.get_absences_report_for_student(student))


class OwnAbsencesEvolution(AbsencesEvolutionBaseView):
    permission_classes = (IsStudent,)

    def get(self, request, *args, **kwargs):
        student = self.request.user.user_profile
        return Response(self.get_absences_report_for_student(student))
