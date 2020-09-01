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
class InactiveTeachersTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = RegisteredSchoolUnitFactory()
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL, school_unit=cls.school)
        cls.url = reverse('statistics:inactive-teachers')

    def test_inactive_teachers_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_inactive_teachers_wrong_user_type(self, user_role):
        school = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(user_role=user_role, school_unit=school)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_teachers_success(self):
        self.client.login(username=self.principal.username, password='passwd')
        expected_fields = ['id', 'full_name', 'last_change_in_catalog']
        today = timezone.now().replace(tzinfo=utc)
        teacher1 = UserProfileFactory(last_change_in_catalog=today - timedelta(days=31), school_unit=self.school, user_role=UserProfile.UserRoles.TEACHER)
        teacher2 = UserProfileFactory(last_change_in_catalog=today - timedelta(days=30), school_unit=self.school, user_role=UserProfile.UserRoles.TEACHER)
        teacher3 = UserProfileFactory(last_change_in_catalog=today - timedelta(days=15), school_unit=self.school, user_role=UserProfile.UserRoles.TEACHER)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertCountEqual(response.data['results'][0].keys(), expected_fields)
        self.assertEqual(response.data['results'][0]['id'], teacher2.id)
        self.assertEqual(response.data['results'][1]['id'], teacher1.id)
