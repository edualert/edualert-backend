from django.db.models.functions import Lower
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from edualert.common.permissions import IsAdministrator
from edualert.common.search_and_filters import CommonSearchFilter
from edualert.schools.models import RegisteredSchoolUnit, SchoolUnit, SchoolUnitCategory, SchoolUnitProfile
from edualert.schools.serializers import SchoolUnitCategorySerializer, SchoolUnitProfileSerializer


class DistrictList(APIView):
    permission_classes = (IsAdministrator,)

    def get(self, request, *args, **kwargs):
        registered_schools = request.query_params.get('registered_schools') == 'true'
        search = request.query_params.get('search', '')

        school_type = RegisteredSchoolUnit if registered_schools else SchoolUnit
        districts = list(school_type.objects.filter(
            district__icontains=search
        ).order_by(
            'district'
        ).values_list(
            'district', flat=True
        ).distinct())

        return Response(data=districts)


class CityByDistrictList(APIView):
    permission_classes = (IsAdministrator,)

    def get(self, request, *args, **kwargs):
        registered_schools = request.query_params.get('registered_schools') == 'true'
        search = request.query_params.get('search', '')

        school_type = RegisteredSchoolUnit if registered_schools else SchoolUnit
        cities = list(school_type.objects.filter(
            district=self.kwargs['district'],
            city__icontains=search
        ).order_by(
            'city'
        ).values_list(
            'city', flat=True
        ).distinct())

        return Response(data=cities)


class SchoolUnitCategoryList(ListAPIView):
    permission_classes = (IsAdministrator,)
    pagination_class = None
    serializer_class = SchoolUnitCategorySerializer

    def get_queryset(self):
        return SchoolUnitCategory.objects.order_by(Lower('name'))


class SchoolUnitProfileList(ListAPIView):
    permission_classes = (IsAdministrator,)
    pagination_class = None
    serializer_class = SchoolUnitProfileSerializer
    search_fields = ['name', ]
    filter_backends = [CommonSearchFilter, ]

    def get_queryset(self):
        return SchoolUnitProfile.objects.filter(**self.get_filters()).order_by(Lower('name'))

    def get_filters(self):
        categories = self.request.GET.getlist('category')
        if not categories:
            return {}

        try:
            categories_ids = [int(category) for category in categories]
        except ValueError:
            return {}

        return {'category_id__in': categories_ids}
