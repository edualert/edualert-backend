import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext as _
from oauth2_provider.models import AccessToken, RefreshToken
from rest_framework import generics, views, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from edualert.common.constants import GET, PUT, HEAD, OPTIONS
from edualert.common.models import AccessKey
from edualert.common.throttle import PasswordViewsScopedRateThrottle
from edualert.common.validators import PasswordValidator
from edualert.profiles.models import UserProfile
from edualert.profiles.serializers import MyAccountStudentSerializer, MyAccountParentSerializer, MyAccountSerializer
from edualert.profiles.tasks import send_reset_password_message


class MyAccountDetail(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    http_method_names = [GET.lower(), PUT.lower(), HEAD.lower(), OPTIONS.lower()]

    def get_serializer_class(self):
        user_role = self.request.user.user_profile.user_role

        if user_role == UserProfile.UserRoles.STUDENT:
            return MyAccountStudentSerializer
        if user_role == UserProfile.UserRoles.PARENT:
            return MyAccountParentSerializer
        return MyAccountSerializer

    def get_object(self):
        return self.request.user.user_profile


class ForgotPassword(views.APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PasswordViewsScopedRateThrottle,)

    @staticmethod
    def make_reset_link(profile):
        # generate the token
        tok = AccessKey.create_key(profile.user, availability=datetime.timedelta(hours=24))
        return '{}{}{}/'.format(settings.FRONTEND_URL, 'reset-password/', tok)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username', None)

        if username is not None and username != '':
            try:
                profile = UserProfile.objects.get(username=username)
            except ObjectDoesNotExist:
                return Response({'message': _('There is no account for this username.')}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'username': [_('This field is required.')]}, status=status.HTTP_400_BAD_REQUEST)

        link = self.make_reset_link(profile)
        send_reset_password_message.delay(profile.id, link)

        return Response()


class SetPassword(views.APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (PasswordViewsScopedRateThrottle,)

    def get_access_key(self):
        token = self.kwargs['access_key']

        try:
            access_key = AccessKey.get_by_token(token)
            if access_key.is_expired():
                return
        except ObjectDoesNotExist:
            return

        return access_key

    @staticmethod
    def reset_password(user, new_password):
        # Delete all tokens & Refresh tokens for this users
        AccessToken.objects.filter(user=user).delete()
        RefreshToken.objects.filter(user=user).delete()

        user.set_password(new_password)
        user.save()

    def post(self, request, *args, **kwargs):
        access_key = self.get_access_key()
        if not access_key:
            return Response({"message": _("Invalid access key.")}, status=status.HTTP_400_BAD_REQUEST)

        user_to_update = access_key.user
        new_password = request.data.get('new_password', None)

        if new_password is not None:
            try:
                PasswordValidator(new_password)
            except ValidationError:
                return Response({'new_password': [PasswordValidator.message]}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'new_password': [_('This field is required.')]}, status=status.HTTP_400_BAD_REQUEST)

        self.reset_password(user_to_update, new_password)
        # Delete the user's access keys, so he/she cannot make another set password request
        access_key_set = AccessKey.objects.filter(user=user_to_update)
        for a_key in access_key_set:
            a_key.expire()

        return Response()
