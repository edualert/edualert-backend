import datetime

from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.common.models import AccessKey
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class SetPasswordTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_unit = RegisteredSchoolUnitFactory()
        cls.profile = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit)
        cls.token = AccessKey.create_key(cls.profile.user, availability=datetime.timedelta(hours=24))
        cls.url = reverse('users:set-password', kwargs={'access_key': cls.token})

    def setUp(self):
        self.token = AccessKey.create_key(self.profile.user, availability=datetime.timedelta(hours=24))
        self.url = reverse('users:set-password', kwargs={'access_key': self.token})

    def test_set_password_invalid_access_key(self):
        # expired access key
        access_key = AccessKey.get_by_token(self.token)
        access_key.expire()

        response = self.client.post(self.url, {'new_password': 'passwd'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Invalid access key.')

        # access key not found
        self.url = reverse('users:set-password', kwargs={'access_key': 'abcdef'})

        response = self.client.post(self.url, {'new_password': 'passwd'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Invalid access key.')

    def test_set_password_no_password(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_password'], ['This field is required.'])

    @data(
        'x' * 5,
        'x' * 129,
        'xyz abc',
    )
    def test_set_password_invalid_password(self, new_pass):
        response = self.client.post(self.url, {'new_password': new_pass})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['new_password'], ['Invalid format. Must be minimum 6, maximum 128 characters, no spaces allowed.'])

    def test_set_password_success(self):
        response = self.client.post(self.url, {'new_password': 'new_passwd'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.profile.user.refresh_from_db()
        self.assertTrue(self.profile.user.check_password('new_passwd'))
        self.assertTrue(AccessKey.get_by_token(self.token).is_expired())

