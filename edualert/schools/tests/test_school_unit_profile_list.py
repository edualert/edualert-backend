from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitProfileFactory


@ddt
class SchoolUnitProfileListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.url = reverse('schools:school-unit-profile-list')

    def test_school_unit_profile_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_school_unit_profile_list_wrong_user_type(self, user_role):
        school_unit = RegisteredSchoolUnitFactory()
        profile = UserProfileFactory(user_role=user_role, school_unit=school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_unit_profile_list_empty(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_school_unit_profile_list_success(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        profile1 = SchoolUnitProfileFactory(name='profile 2')
        profile2 = SchoolUnitProfileFactory(name='profile 3')
        profile3 = SchoolUnitProfileFactory(name='profile 1')
        profile4 = SchoolUnitProfileFactory(name='profile 4', category=profile3.category)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data
        self.assertEqual(len(results), 4)
        self.assertEqual(profile3.id, results[0]['id'])
        self.assertEqual(profile1.id, results[1]['id'])
        self.assertEqual(profile2.id, results[2]['id'])
        self.assertEqual(profile4.id, results[3]['id'])

        expected_fields = ['id', 'name']
        for result in results:
            self.assertCountEqual(result.keys(), expected_fields)

        # Search by name
        response = self.client.get(self.url, {'search': 'profile 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(profile3.id, response.data[0]['id'])

        # Filter by one category
        response = self.client.get(self.url, {'category': profile3.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 2)
        self.assertEqual(profile3.id, response.data[0]['id'])
        self.assertEqual(profile4.id, response.data[1]['id'])

        # Filter by multiple category
        response = self.client.get(self.url + '?category={}&category={}'.format(profile1.category.id, profile2.category.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 2)
        self.assertEqual(profile1.id, response.data[0]['id'])
        self.assertEqual(profile2.id, response.data[1]['id'])
