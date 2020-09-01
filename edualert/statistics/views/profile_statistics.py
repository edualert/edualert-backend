from datetime import timedelta

from django.db.models.functions import Lower
from django.http import Http404
from django.utils import timezone
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.common.permissions import IsPrincipal, IsTeacher
from edualert.profiles.models import UserProfile
from edualert.statistics.pagination import StatisticsPagination
from edualert.statistics.serializers import UserProfileLastChangeInCatalogSerializer, ParentLastOnlineSerializer


class InactiveTeachers(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    pagination_class = StatisticsPagination
    serializer_class = UserProfileLastChangeInCatalogSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(
            user_role=UserProfile.UserRoles.TEACHER,
            school_unit_id=self.request.user.user_profile.school_unit_id,
            last_change_in_catalog__lt=timezone.now() - timedelta(days=30)
        ).order_by(
            '-last_change_in_catalog',
            Lower('full_name')
        )


class InactiveParents(generics.ListAPIView):
    permission_classes = (IsTeacher,)
    pagination_class = StatisticsPagination
    serializer_class = ParentLastOnlineSerializer

    def get_queryset(self):
        teacher = self.request.user.user_profile
        current_calendar = get_current_academic_calendar()
        if not current_calendar:
            raise Http404()

        current_mastering_class = get_object_or_404(
            teacher.mastering_study_classes,
            academic_year=current_calendar.academic_year
        )

        return UserProfile.objects.filter(
            child__student_in_class=current_mastering_class,
            user_role=UserProfile.UserRoles.PARENT,
            school_unit_id=teacher.school_unit_id,
            last_online__lt=timezone.now() - timedelta(days=30)
        ).order_by(
            '-last_online',
            Lower('full_name')
        )
