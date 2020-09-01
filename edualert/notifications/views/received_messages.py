from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from edualert.common.pagination import CommonPagination
from edualert.common.permissions import IsParentOrStudent
from edualert.common.search_and_filters import CommonSearchFilter
from edualert.notifications.models import TargetUserThrough
from edualert.notifications.serializers import ReceivedNotificationListSerializer, ReceivedNotificationDetailSerializer
from edualert.notifications.views.sent_messages import get_date_filter


class MyReceivedMessageList(generics.ListAPIView):
    permission_classes = (IsParentOrStudent,)
    pagination_class = CommonPagination
    search_fields = ['notification__title', 'notification__from_user_full_name']
    filter_backends = [CommonSearchFilter]
    serializer_class = ReceivedNotificationListSerializer

    def get_queryset(self):
        profile = self.request.user.user_profile
        created = self.request.query_params.get('created')
        created_filter = get_date_filter('notification__created', created) if created else {}

        return profile.target_users_through.filter(
            **created_filter
        ).select_related(
            'notification'
        ).order_by('-notification__created')


class MyReceivedMessageDetail(generics.RetrieveAPIView):
    permission_classes = (IsParentOrStudent,)
    lookup_field = 'id'
    serializer_class = ReceivedNotificationDetailSerializer

    def get_queryset(self):
        profile = self.request.user.user_profile
        return profile.target_users_through.select_related('notification')


class MyReceivedMessageMarkAsRead(APIView):
    permission_classes = (IsParentOrStudent,)

    def get_queryset(self):
        profile = self.request.user.user_profile
        return profile.target_users_through.select_related('notification')

    def post(self, request, *args, **kwargs):
        profile = self.request.user.user_profile

        target_user_through = get_object_or_404(
            TargetUserThrough.objects.select_related('notification'),
            id=self.kwargs['id'],
            user_profile_id=profile.id
        )

        target_user_through.is_read = True
        target_user_through.save()

        return Response(
            ReceivedNotificationDetailSerializer(target_user_through).data
        )
