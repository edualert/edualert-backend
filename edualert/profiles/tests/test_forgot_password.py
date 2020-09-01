from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.common.models import AccessKey
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


class ForgotPasswordTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.profile = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.url = reverse('users:forgot-password')

    def test_forgot_password_no_username(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['username'], ['This field is required.'])

    def test_forgot_password_user_not_found(self):
        response = self.client.post(self.url, {'username': 'someUsernameThatDoesntExist'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'There is no account for this username.')

    @patch('edualert.profiles.tasks.send_mail')
    @patch('edualert.profiles.tasks.send_sms')
    def test_forgot_password_send_email(self, send_sms_mock, send_mail_mock):
        response = self.client.post(self.url, {'username': self.profile.username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(AccessKey.objects.filter(user=self.profile.user).count(), 1)

        self.assertEqual(send_mail_mock.call_count, 1)
        self.assertEqual(send_sms_mock.call_count, 0)

    @patch('edualert.profiles.tasks.send_mail')
    @patch('edualert.profiles.tasks.send_sms')
    def test_forgot_password_send_sms(self, send_sms_mock, send_mail_mock):
        self.profile.use_phone_as_username = True
        self.profile.save()

        response = self.client.post(self.url, {'username': self.profile.username})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(AccessKey.objects.filter(user=self.profile.user).count(), 1)

        self.assertEqual(send_mail_mock.call_count, 0)
        self.assertEqual(send_sms_mock.call_count, 1)
