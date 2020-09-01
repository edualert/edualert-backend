from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from edualert.common.permissions import IsAdministratorOrPrincipal
from edualert.profiles.models import Label
from edualert.profiles.serializers import LabelSerializer


class LabelList(generics.ListAPIView):
    permission_classes = (IsAdministratorOrPrincipal,)
    pagination_class = None
    filterset_fields = ['user_role', ]
    filter_backends = [DjangoFilterBackend, ]
    serializer_class = LabelSerializer
    queryset = Label.objects.all()
