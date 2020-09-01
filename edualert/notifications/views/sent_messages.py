import datetime

from django.db.models import Count, Q
from rest_framework import generics

from edualert.common.constants import POST
from edualert.common.pagination import CommonPagination
from edualert.common.permissions import IsTeacherOrPrincipal
from edualert.common.search_and_filters import CommonSearchFilter
from edualert.notifications.models import Notification
from edualert.notifications.serializers import SentNotificationListSerializer, SentNotificationDetailSerializer, SentNotificationCreateSerializer


def get_date_filter(param_key, param_value):
    created_filter = {}

    try:
        date_filter = datetime.datetime.strptime(param_value, '%d-%m-%Y')
        created_filter = {'{}__date'.format(param_key): date_filter}
    except ValueError:
        pass

    return created_filter


class MySentMessageList(generics.ListCreateAPIView):
    permission_classes = (IsTeacherOrPrincipal,)
    pagination_class = CommonPagination
    search_fields = ['title', 'target_user_through__user_profile_full_name']
    filter_backends = [CommonSearchFilter, ]

    def get_serializer_class(self):
        if self.request.method == POST:
            return SentNotificationCreateSerializer
        return SentNotificationListSerializer

    def get_queryset(self):
        created = self.request.query_params.get('created')
        created_filter = {}
        if created:
            created_filter = get_date_filter('created', created)

        return Notification.objects.select_related('target_study_class') \
            .filter(from_user=self.request.user.user_profile, **created_filter) \
            .annotate(read_by_count=Count('target_user_through', filter=Q(target_user_through__is_read=True)))


class MySentMessageDetail(generics.RetrieveAPIView):
    permission_classes = (IsTeacherOrPrincipal,)
    serializer_class = SentNotificationDetailSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Notification.objects.select_related('target_study_class') \
            .filter(from_user=self.request.user.user_profile) \
            .annotate(read_by_count=Count('target_user_through', filter=Q(target_user_through__is_read=True)))
