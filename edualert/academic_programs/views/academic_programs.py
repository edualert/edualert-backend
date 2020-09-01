import datetime
from methodtools import lru_cache

from django.db.models import Q
from django.db.models.functions import Lower
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.academic_programs.models import AcademicProgram
from edualert.academic_programs.serializers import AcademicProgramListSerializer, AcademicProgramDetailSerializer, \
    AcademicProgramCreateSerializer, AcademicProgramUpdateSerializer
from edualert.common.constants import POST, PATCH, GET, OPTIONS, HEAD, DELETE
from edualert.common.pagination import CommonPagination
from edualert.common.permissions import IsPrincipal
from edualert.common.search_and_filters import CommonSearchFilter
from edualert.study_classes.constants import CATEGORY_LEVELS_CLASS_MAPPING
from edualert.subjects.models import ProgramSubjectThrough
from edualert.subjects.serializers import SimpleProgramSubjectThroughSerializer


class AcademicProgramList(generics.ListCreateAPIView):
    permission_classes = (IsPrincipal,)
    serializer_class = AcademicProgramListSerializer
    pagination_class = CommonPagination
    search_fields = ['name', ]
    filter_backends = [CommonSearchFilter]

    def get_serializer_class(self):
        if self.request.method == POST:
            return AcademicProgramCreateSerializer
        return AcademicProgramListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'academic_year': self.kwargs['academic_year'],
            'school_unit': self.request.user.user_profile.school_unit
        })
        return context

    def get_queryset(self):
        profile = self.request.user.user_profile

        filters = {
            'academic_year': self.kwargs['academic_year'],
            'school_unit_id': profile.school_unit_id
        }
        class_grade = self.request.query_params.get('class_grade')
        if class_grade:
            category_level = CATEGORY_LEVELS_CLASS_MAPPING.get(class_grade)
            if category_level:
                category = profile.school_unit.categories.filter(category_level=category_level).first()
                filters['generic_academic_program__category'] = category

        return AcademicProgram.objects.filter(
            **filters
        ).order_by(Lower('name'))

    def create(self, request, *args, **kwargs):
        current_academic_year_calendar = get_current_academic_calendar()

        if not current_academic_year_calendar:
            raise Http404()

        if current_academic_year_calendar.academic_year != kwargs['academic_year']:
            return Response({'message': _('Invalid year, must be the current academic year.')}, status=status.HTTP_400_BAD_REQUEST)

        # TODO uncomment after it's tested
        # if timezone.now().date() > datetime.date(current_academic_year_calendar.created.year, 9, 15):
        #     return Response(
        #         {'message': _('Academic programs must be created before 15th of september of the current year.')},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        return super().create(request, *args, **kwargs)


class AcademicProgramDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsPrincipal,)
    lookup_field = 'id'
    http_method_names = [GET.lower(), PATCH.lower(), DELETE.lower(), OPTIONS.lower(), HEAD.lower()]

    def get_serializer_class(self):
        if self.request.method == PATCH:
            return AcademicProgramUpdateSerializer
        return AcademicProgramDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'generic_academic_program_id': self.get_object().generic_academic_program_id,
            'academic_year': self.get_object().academic_year,
            'school_unit': self.request.user.user_profile.school_unit
        })
        return context

    def get_queryset(self):
        return AcademicProgram.objects.filter(school_unit=self.request.user.user_profile.school_unit)

    @lru_cache(maxsize=None)
    def get_object(self):
        return super().get_object()

    def delete(self, request, *args, **kwargs):
        program = self.get_object()
        if program.classes_count > 0:
            return Response({'message': _("Cannot delete an academic program that still has study classes assigned.")},
                            status=status.HTTP_400_BAD_REQUEST)

        return self.destroy(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        current_academic_year_calendar = get_current_academic_calendar()

        if not current_academic_year_calendar:
            raise Http404()

        if current_academic_year_calendar.academic_year != self.get_object().academic_year:
            return Response({'message': _('Invalid year, must be the current academic year.')}, status=status.HTTP_400_BAD_REQUEST)

        # TODO uncomment after it's tested
        # if timezone.now().date() > datetime.date(current_academic_year_calendar.created.year, 9, 15):
        #     return Response(
        #         {'message': _('Academic programs must be updated before 15th of September of the current year.')},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        return super().partial_update(request, *args, **kwargs)


class AcademicProgramSubjectList(APIView):
    permission_classes = (IsPrincipal,)

    def get_queryset(self, class_grade):
        academic_program = get_object_or_404(AcademicProgram, id=self.kwargs.get('id'))
        return ProgramSubjectThrough.objects.filter(
            Q(academic_program_id=academic_program.id) | Q(generic_academic_program_id=academic_program.generic_academic_program_id),
            class_grade=class_grade
        ).order_by(Lower('subject_name'))

    def get(self, *args, **kwargs):
        class_grade = self.request.query_params.get('grade')
        if not class_grade:
            return Response({'class_grade': [_('grade query param is missing.')]}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset(class_grade)

        return Response(
            SimpleProgramSubjectThroughSerializer(instance=queryset, many=True).data
        )
