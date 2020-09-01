from rest_framework import generics

from edualert.common.permissions import IsPrincipal
from edualert.common.search_and_filters import CommonSearchFilter
from edualert.subjects.models import Subject
from edualert.subjects.serializers import SubjectSerializer


class SubjectList(generics.ListAPIView):
    permission_classes = (IsPrincipal,)
    pagination_class = None
    search_fields = ['name', ]
    filter_backends = [CommonSearchFilter, ]
    serializer_class = SubjectSerializer
    queryset = Subject.objects.filter(should_be_in_taught_subjects=True) \
        .exclude(is_coordination=True)
