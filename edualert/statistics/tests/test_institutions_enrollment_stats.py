import datetime
from unittest.mock import patch

from ddt import data, ddt
from django.urls import reverse
from pytz import utc
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.statistics.factories import SchoolUnitEnrollmentStatsFactory


@ddt
class InstitutionsEnrollmentStatsTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.calendar = AcademicYearCalendarFactory()
        cls.stats = SchoolUnitEnrollmentStatsFactory(month=10, daily_statistics=[{'day': 1, 'weekday': 'Lu', 'count': 1}])
        cls.url = reverse('statistics:institutions-enrollment-stats')

    def test_institutions_enrollment_stats_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT,
    )
    def test_school_unit_enrollment_stats_wrong_user_type(self, user_role):
        user = UserProfileFactory(user_role=user_role, school_unit=RegisteredSchoolUnitFactory())
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @data(13, -1, 0, '-', 'november')
    @patch('django.utils.timezone.now', return_value=datetime.datetime(2020, 10, 1).replace(tzinfo=utc))
    def test_school_unit_enrollment_stats_invalid_month(self, month, mocked_method):
        self.client.login(username=self.admin.username, password='passwd')
        response = self.client.get(self.url, {'month': month})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('django.utils.timezone.now', return_value=datetime.datetime(2020, 10, 1).replace(tzinfo=utc))
    def test_school_unit_enrollment_stats_month_param(self, mocked_method):
        self.client.login(username=self.admin.username, password='passwd')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.url, {'month': 9})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_school_unit_enrollment_stats_success(self):
        self.client.login(username=self.admin.username, password='passwd')
        expected_fields = ['day', 'weekday', 'count']
        response = self.client.get(self.url, {'month': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertCountEqual(response.data[0].keys(), expected_fields)
