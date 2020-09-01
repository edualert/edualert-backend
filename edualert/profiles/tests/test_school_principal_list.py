from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class SchoolPrincipalListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.url = reverse('users:school-principal-list')

    def test_school_principal_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_school_principal_list_wrong_user_type(self, user_role):
        school_unit = RegisteredSchoolUnitFactory()
        profile = UserProfileFactory(user_role=user_role, school_unit=school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_principal_list(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        profile1 = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, full_name='John Doe')
        profile2 = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, full_name='Jane Doe')
        UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, is_active=False)

        RegisteredSchoolUnitFactory(school_principal=profile2)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([profile2.id, profile1.id], [profile['id'] for profile in response.data])

        expected_fields = ['id', 'full_name', 'username']
        for profile in response.data:
            self.assertCountEqual(profile.keys(), expected_fields)

        response = self.client.get(self.url, {'search': 'Jane'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([profile2.id, ], [profile['id'] for profile in response.data])

        response = self.client.get(self.url, {'has_school': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([profile1.id, ], [profile['id'] for profile in response.data])

        response = self.client.get(self.url, {'has_school': 'false', 'search': 'Jane'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
