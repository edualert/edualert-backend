from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import SchoolUnitFactory, RegisteredSchoolUnitFactory


@ddt
class CityByDistrictListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)

    @staticmethod
    def build_url(district='Cluj'):
        return reverse('schools:city-by-district-list', kwargs={'district': district})

    def test_city_by_district_list_unauthenticated(self):
        response = self.client.get(self.build_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_city_by_district_list_wrong_user_type(self, user_role):
        school_unit = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(user_role=user_role, school_unit=school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_city_by_district_list_school_units(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        # Create a few school units
        su1 = SchoolUnitFactory(district='Cluj', city='Cluj-Napoca')
        su2 = SchoolUnitFactory(district='Cluj', city='Dej')
        SchoolUnitFactory(district='Cluj', city='Cluj-Napoca')
        SchoolUnitFactory(district='Bihor', city='Oradea')

        response = self.client.get(self.build_url('Cluj'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data, [su1.city, su2.city])

        # Search by city name
        response = self.client.get(self.build_url('Cluj'), {'search': 'Cl'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data, [su1.city, ])

    def test_city_by_district_list_registered_school_units(self):
        self.client.login(username=self.admin_user.username, password='passwd')
        # Create some registered school units
        rsu1 = RegisteredSchoolUnitFactory(district='Cluj', city='Cluj-Napoca')
        rsu2 = RegisteredSchoolUnitFactory(district='Cluj', city='Dej')
        RegisteredSchoolUnitFactory(district='Cluj', city='Cluj-Napoca')
        RegisteredSchoolUnitFactory(district='Bihor', city='Oradea')

        # First test that registered school units aren't returned without the query param
        response = self.client.get(self.build_url('Cluj'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        # Now send the registered_schools param
        response = self.client.get(self.build_url('Cluj'), {'registered_schools': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data, [rsu1.city, rsu2.city])

        # Search by district name
        response = self.client.get(self.build_url('Cluj'), {'registered_schools': 'true', 'search': 'De'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data, [rsu2.city, ])
