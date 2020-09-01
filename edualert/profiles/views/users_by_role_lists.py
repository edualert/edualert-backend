from django.db.models.functions import Lower
from rest_framework import generics

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.common.permissions import IsAdministrator, IsTeacherOrPrincipal, IsPrincipal
from edualert.common.search_and_filters import CommonSearchFilter
from edualert.profiles.models import UserProfile
from edualert.profiles.serializers import UserProfileWithUsernameSerializer, UserProfileBaseSerializer, \
    UserProfileWithTaughtSubjectsSerializer


class SchoolPrincipalList(generics.ListAPIView):
    permission_classes = (IsAdministrator,)
    serializer_class = UserProfileWithUsernameSerializer
    pagination_class = None
    search_fields = ['full_name', ]
    filter_backends = [CommonSearchFilter, ]

    def get_queryset(self):
        profiles = UserProfile.objects.filter(is_active=True, user_role=UserProfile.UserRoles.PRINCIPAL) \
            .order_by(Lower('full_name'))

        if self.request.query_params.get('has_school') == 'false':
            # Return only the school principals that don't have a school assigned yet.
            profiles = profiles.filter(registered_school_unit__isnull=True)

        return profiles


class ParentList(generics.ListAPIView):
    permission_classes = (IsTeacherOrPrincipal,)
    serializer_class = UserProfileBaseSerializer
    pagination_class = None
    search_fields = ['full_name', ]
    filter_backends = [CommonSearchFilter]

    def get_queryset(self):
        profile = self.request.user.user_profile
        queryset = UserProfile.objects.filter(user_role=UserProfile.UserRoles.PARENT,
                                              is_active=True, school_unit=profile.school_unit) \
            .order_by(Lower('full_name'))

        if profile.user_role == UserProfile.UserRoles.TEACHER:
            queryset = queryset.filter(
                child__student_in_class__teachers=profile
            ).distinct()

        return queryset


class TeacherList(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    serializer_class = UserProfileWithTaughtSubjectsSerializer
    pagination_class = None
    search_fields = ['full_name', ]
    filter_backends = [CommonSearchFilter]

    def get_queryset(self):
        profile = self.request.user.user_profile
        queryset = UserProfile.objects.filter(user_role=UserProfile.UserRoles.TEACHER,
                                              is_active=True, school_unit=profile.school_unit) \
            .order_by(Lower('full_name'))

        if self.request.query_params.get('is_class_master') == 'false':
            # Return only the teachers that don't have a class assigned yet.
            current_calendar = get_current_academic_calendar()
            if not current_calendar:
                return queryset
            queryset = queryset.exclude(mastering_study_classes__academic_year=current_calendar.academic_year)

        return queryset


class StudentList(generics.ListAPIView):
    permission_classes = (IsTeacherOrPrincipal,)
    serializer_class = UserProfileBaseSerializer
    pagination_class = None
    search_fields = ['full_name', ]
    filter_backends = [CommonSearchFilter]

    def get_queryset(self):
        has_class = self.request.query_params.get('has_class')

        profile = self.request.user.user_profile
        queryset = UserProfile.objects.filter(user_role=UserProfile.UserRoles.STUDENT, is_active=True) \
            .order_by(Lower('full_name'))

        if profile.user_role == UserProfile.UserRoles.PRINCIPAL:
            queryset = queryset.filter(
                school_unit=profile.school_unit
            ).distinct()

            if has_class == 'false':
                queryset = queryset.filter(student_in_class__isnull=True)
        else:
            if has_class == 'false':
                return UserProfile.objects.none()

            queryset = queryset.filter(
                student_in_class__teachers=profile
            ).distinct()

        return queryset
