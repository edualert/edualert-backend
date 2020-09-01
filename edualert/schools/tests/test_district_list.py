from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import SchoolUnitFactory, RegisteredSchoolUnitFactory


@ddt
class DistrictListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.url = reverse('schools:district-list')

    def test_district_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_district_list_wrong_user_type(self, user_role):
        school_unit = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(user_role=user_role, school_unit=school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_district_list_school_units(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        # Create a few school units
        su1 = SchoolUnitFactory(district='Bihor')
        su2 = SchoolUnitFactory(district='Cluj')
        SchoolUnitFactory(district='Cluj')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data, [su1.district, su2.district])

        # Search by district name
        response = self.client.get(self.url, {'search': 'Cl'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data, [su2.district, ])

    def test_district_list_registered_school_units(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        # Create some registered school units
        rsu1 = RegisteredSchoolUnitFactory(district='Bihor')
        rsu2 = RegisteredSchoolUnitFactory(district='Cluj')
        RegisteredSchoolUnitFactory(district='Cluj')

        # First test that registered school units aren't returned without the query param
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        # Now send the registered_schools param
        response = self.client.get(self.url, {'registered_schools': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data, [rsu1.district, rsu2.district])

        # Search by district name
        response = self.client.get(self.url, {'registered_schools': 'true', 'search': 'Bi'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data, [rsu1.district, ])
