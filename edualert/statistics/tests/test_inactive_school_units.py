from datetime import timedelta

from ddt import ddt, data
from django.urls import reverse
from django.utils import timezone
from pytz import utc
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class InactiveSchoolUnitsTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.url = reverse('statistics:inactive-school-units')

    def test_inactive_school_units_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_inactive_school_units_wrong_user_type(self, user_role):
        school = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(user_role=user_role, school_unit=school)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_school_units_success(self):
        self.client.login(username=self.admin.username, password='passwd')
        expected_fields = ['id', 'name', 'last_change_in_catalog']
        today = timezone.now().replace(tzinfo=utc)
        school1 = RegisteredSchoolUnitFactory(last_change_in_catalog=today - timedelta(days=31))
        school2 = RegisteredSchoolUnitFactory(last_change_in_catalog=today - timedelta(days=30))
        school3 = RegisteredSchoolUnitFactory(last_change_in_catalog=today - timedelta(days=15))

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertCountEqual(response.data['results'][0].keys(), expected_fields)
        self.assertEqual(response.data['results'][0]['id'], school2.id)
        self.assertEqual(response.data['results'][1]['id'], school1.id)
