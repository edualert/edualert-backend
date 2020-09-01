from ddt import data, ddt
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class RegisteredSchoolUnitsDeactivateTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.rsu = RegisteredSchoolUnitFactory()
        cls.url = reverse('schools:school-unit-deactivate', kwargs={'id': cls.rsu.id})

    def test_registered_school_unit_deactivate_unauthenticated(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_registered_school_unit_deactivate_wrong_user_type(self, user_role):
        user = UserProfileFactory(user_role=user_role, school_unit=self.rsu)
        self.client.login(username=user.username, password='passwd')

        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_registered_school_unit_deactivate_not_found(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        url = reverse('schools:school-unit-deactivate', kwargs={'id': 0})

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_registered_school_unit_deactivate_success(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = ['id', 'is_active', 'categories', 'academic_profile', 'address',
                           'phone_number', 'email', 'district', 'city', 'name', 'school_principal']
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.rsu.refresh_from_db()
        self.assertFalse(self.rsu.is_active)

        # Check that the school principal cannot log in anymore
        principal = self.rsu.school_principal
        self.assertFalse(self.client.login(username=principal.username, password='passwd'))

    def test_registered_school_unit_deactivate_users_logged_out(self):
        principal = self.rsu.school_principal
        client2 = APIClient()
        client2.login(username=principal.username, password='passwd')

        self.client.login(username=self.admin_user.username, password='passwd')
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the user was logged out
        response = client2.get(reverse('users:user-profile-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registered_school_unit_deactivate_already_active(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        self.rsu.is_active = False
        self.rsu.save()

        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'This school unit is already inactive.')
