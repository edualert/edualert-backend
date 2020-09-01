from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class SchoolUnitsAtRiskTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.url = reverse('statistics:school-units-at-risk')

    def test_school_units_at_risk_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_school_units_at_risk_wrong_user_type(self, user_role):
        school = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(user_role=user_role, school_unit=school)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_units_at_risk_success(self):
        self.client.login(username=self.admin.username, password='passwd')

        school1 = RegisteredSchoolUnitFactory(students_at_risk_count=3)
        school2 = RegisteredSchoolUnitFactory(students_at_risk_count=2, name='b')
        school3 = RegisteredSchoolUnitFactory(students_at_risk_count=2, name='a')
        school4 = RegisteredSchoolUnitFactory(students_at_risk_count=4)
        RegisteredSchoolUnitFactory()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)
        self.assertCountEqual(response.data['results'][0].keys(), ['id', 'name', 'students_at_risk_count'])

        self.assertEqual(response.data['results'][0]['id'], school4.id)
        self.assertEqual(response.data['results'][1]['id'], school1.id)
        self.assertEqual(response.data['results'][2]['id'], school3.id)
        self.assertEqual(response.data['results'][3]['id'], school2.id)
