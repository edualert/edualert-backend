from django.db.models.functions import Lower
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from oauth2_provider.models import AccessToken, RefreshToken
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from edualert.common.constants import POST, GET, PUT, OPTIONS, HEAD
from edualert.common.pagination import CommonPagination
from edualert.common.permissions import IsAdministrator, IsPrincipal
from edualert.common.search_and_filters import CommonSearchFilter
from edualert.schools.models import RegisteredSchoolUnit, SchoolUnit
from edualert.schools.serializers import RegisteredSchoolUnitListSerializer, RegisteredSchoolUnitDetailSerializer, \
    UnregisteredSchoolUnitListSerializer, RegisteredSchoolUnitCreateSerializer, RegisteredSchoolUnitUpdateSerializer, \
    RegisteredSchoolUnitNameSerializer


class SchoolUnitList(generics.ListCreateAPIView):
    permission_classes = (IsAdministrator,)
    serializer_class = RegisteredSchoolUnitListSerializer
    filterset_fields = ['district', 'city', 'categories', 'academic_profile', ]
    search_fields = ['name', ]
    filter_backends = [DjangoFilterBackend, CommonSearchFilter]
    pagination_class = CommonPagination

    def get_serializer_class(self):
        if self.request.method == POST:
            return RegisteredSchoolUnitCreateSerializer
        return RegisteredSchoolUnitListSerializer

    def get_queryset(self):
        return RegisteredSchoolUnit.objects.order_by('-is_active', Lower('name'))


class SchoolUnitNameList(generics.ListAPIView):
    permission_classes = (AllowAny,)
    pagination_class = None
    serializer_class = RegisteredSchoolUnitNameSerializer
    filterset_fields = ['is_active', ]
    search_fields = ['name', ]
    filter_backends = [DjangoFilterBackend, CommonSearchFilter]
    queryset = RegisteredSchoolUnit.objects.all().order_by(Lower('name'))


class SchoolUnitDetail(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAdministrator,)
    queryset = RegisteredSchoolUnit.objects.all()
    lookup_field = 'id'
    http_method_names = [GET.lower(), PUT.lower(), OPTIONS.lower(), HEAD.lower()]

    def get_serializer_class(self):
        if self.request.method == PUT:
            return RegisteredSchoolUnitUpdateSerializer
        return RegisteredSchoolUnitDetailSerializer


class SchoolUnitActivate(generics.GenericAPIView):
    permission_classes = (IsAdministrator,)
    serializer_class = RegisteredSchoolUnitDetailSerializer

    def get_object(self):
        return get_object_or_404(RegisteredSchoolUnit, id=self.kwargs['id'])

    def post(self, request, *args, **kwargs):
        school_unit = self.get_object()

        if school_unit.is_active:
            return Response({"message": _("This school unit is already active.")}, status=status.HTTP_400_BAD_REQUEST)

        school_unit.is_active = True
        school_unit.save()

        serializer = self.get_serializer(school_unit)
        return Response(serializer.data)


class SchoolUnitDeactivate(generics.GenericAPIView):
    permission_classes = (IsAdministrator,)
    serializer_class = RegisteredSchoolUnitDetailSerializer

    def get_object(self):
        return get_object_or_404(RegisteredSchoolUnit, id=self.kwargs['id'])

    def post(self, request, *args, **kwargs):
        school_unit = self.get_object()

        if not school_unit.is_active:
            return Response({"message": _("This school unit is already inactive.")}, status=status.HTTP_400_BAD_REQUEST)

        school_unit.is_active = False
        school_unit.save()

        # Delete all tokens & Refresh tokens for this school unit's users
        AccessToken.objects.filter(user__user_profile__school_unit=school_unit).delete()
        RefreshToken.objects.filter(user__user_profile__school_unit=school_unit).delete()

        serializer = self.get_serializer(school_unit)
        return Response(serializer.data)


class UnregisteredSchoolUnitList(generics.ListAPIView):
    permission_classes = (IsAdministrator,)
    serializer_class = UnregisteredSchoolUnitListSerializer
    pagination_class = None
    filterset_fields = ['district', 'city', ]
    search_fields = ['name', ]
    filter_backends = [DjangoFilterBackend, CommonSearchFilter]
    queryset = SchoolUnit.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Only fetch the school units that are not present in the registered school units table
        queryset = queryset.raw("""
            SELECT t1.name, t1.id , t1.city, t1.district
            FROM schools_schoolunit t1 
                left join schools_registeredschoolunit t2 
                    ON t2.name = t1.name AND t2.city = t1.city and t2.district = t1.district
            WHERE  t1.id IN %s AND t2.name IS NULL AND t2.city IS NULL and t2.district IS NULL
        """, [tuple(queryset.values_list('id', flat=True)), ])

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MySchoolUnit(generics.RetrieveAPIView):
    permission_classes = (IsPrincipal,)
    serializer_class = RegisteredSchoolUnitDetailSerializer

    def get_object(self):
        return get_object_or_404(RegisteredSchoolUnit, user_profile=self.request.user.user_profile)
