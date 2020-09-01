from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import SchoolUnitFactory, RegisteredSchoolUnitFactory


@ddt
class UnregisteredSchoolUnitListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.url = reverse('schools:unregistered-school-unit-list')

    def test_unregistered_school_unit_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_unregistered_school_unit_list_wrong_user_type(self, user_role):
        school_unit = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(user_role=user_role, school_unit=school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unregistered_school_unit_list_success(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        # Check the case where no registered school units are found
        su = SchoolUnitFactory(name='school1', city='city1', district='district1')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data[0]['id'], su.id)
        expected_fields = ['id', 'name', 'district', 'city']
        self.assertCountEqual(response.data[0].keys(), expected_fields)

        # Check the case where a registered school unit with the same name district and city exists
        rsu = RegisteredSchoolUnitFactory(name='school1', city='city1', district='district1')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Add a registered school with the same name, but in a different city in the same district
        unique_school = SchoolUnitFactory(name='school1', city='city2', district='district1')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Add a registered school with the same name, and city but different district
        unique_school = SchoolUnitFactory(name='school1', city='city2', district='district3')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


    @data(
        {'city': 'a'},
        {'district': 'b'},
    )
    def test_unregistered_school_list_filters(self, filter):
        self.client.login(username=self.admin_user.username, password='passwd')
        # Check that the uniqueness checks still work even with filters
        su = SchoolUnitFactory(**filter)
        SchoolUnitFactory(**filter)

        response = self.client.get(self.url, filter)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        rsu = RegisteredSchoolUnitFactory(name=su.name, city=su.city, district=su.district)
        response = self.client.get(self.url, filter)
        self.assertEqual(len(response.data), 1)

    def test_unregistered_school_unit_list_search(self):
        self.client.login(username=self.admin_user.username, password='passwd')

        su = SchoolUnitFactory(name='a')
        SchoolUnitFactory(name='b')
        response = self.client.get(self.url, {'search': su.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        rsu = RegisteredSchoolUnitFactory(name=su.name, city=su.city, district=su.district)
        response = self.client.get(self.url, {'search': su.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
