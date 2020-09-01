from rest_framework import generics

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.academic_programs.models import GenericAcademicProgram, AcademicProgram
from edualert.academic_programs.serializers import GenericAcademicProgramSerializer, GenericAcademicProgramDetailSerializer
from edualert.common.permissions import IsPrincipal, IsAdministratorOrSchoolEmployee
from edualert.common.search_and_filters import CommonSearchFilter
from edualert.profiles.models import UserProfile


class UnregisteredAcademicProgramList(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    serializer_class = GenericAcademicProgramSerializer
    pagination_class = None
    search_fields = ['name', ]
    filter_backends = [CommonSearchFilter, ]

    def get_queryset(self):
        try:
            current_academic_year = get_current_academic_calendar().academic_year
        except AttributeError:
            return GenericAcademicProgram.objects.none()

        principal_school = self.request.user.user_profile.school_unit
        exclude_ids = AcademicProgram.objects.filter(academic_year=current_academic_year,
                                                     school_unit=principal_school) \
            .values_list('generic_academic_program_id', flat=True)

        return GenericAcademicProgram.objects.filter(academic_profile=principal_school.academic_profile,
                                                     category_id__in=principal_school.categories.values_list('id', flat=True)) \
            .exclude(id__in=exclude_ids)


class GenericAcademicProgramList(generics.ListAPIView):
    permission_classes = (IsAdministratorOrSchoolEmployee,)
    serializer_class = GenericAcademicProgramSerializer
    pagination_class = None
    search_fields = ['name', ]
    filter_backends = [CommonSearchFilter, ]

    def get_queryset(self):
        user_profile = self.request.user.user_profile

        if user_profile.user_role == UserProfile.UserRoles.ADMINISTRATOR:
            return GenericAcademicProgram.objects.all()

        school_unit = user_profile.school_unit
        return GenericAcademicProgram.objects.filter(academic_profile=school_unit.academic_profile,
                                                     category_id__in=school_unit.categories.values_list('id', flat=True))


class GenericAcademicProgramDetail(generics.RetrieveAPIView):
    permission_classes = (IsPrincipal,)
    lookup_field = 'id'
    serializer_class = GenericAcademicProgramDetailSerializer

    def get_queryset(self):
        return GenericAcademicProgram.objects.filter(academic_profile=self.request.user.user_profile.school_unit.academic_profile)
