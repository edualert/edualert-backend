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
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class AcademicProgramsAbsencesTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.calendar = AcademicYearCalendarFactory()
        cls.url = reverse('statistics:program-absences')
        cls.expected_fields = ['id', 'name', 'unfounded_abs_avg_sem1', 'unfounded_abs_avg_annual']

    def test_academic_programs_absences_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_academic_programs_absences_wrong_user_type(self, user_role):
        school = RegisteredSchoolUnitFactory()
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=school if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('django.utils.timezone.now', return_value=datetime.datetime(2019, 12, 10).replace(tzinfo=utc))
    def test_academic_programs_absences_first_semester(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')
        AcademicProgramFactory(unfounded_abs_avg_sem1=1, unfounded_abs_avg_annual=3, school_unit=self.school_unit)
        AcademicProgramFactory(unfounded_abs_avg_sem1=2, unfounded_abs_avg_annual=2, school_unit=self.school_unit)
        AcademicProgramFactory(unfounded_abs_avg_sem1=3, unfounded_abs_avg_annual=1, school_unit=self.school_unit)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        for result in response.data['results']:
            self.assertCountEqual(result.keys(), self.expected_fields)
        self.assertEqual(response.data['results'][0]['unfounded_abs_avg_sem1'], 3)
        self.assertEqual(response.data['results'][1]['unfounded_abs_avg_sem1'], 2)
        self.assertEqual(response.data['results'][2]['unfounded_abs_avg_sem1'], 1)

    @patch('django.utils.timezone.now', return_value=datetime.datetime(2020, 8, 8).replace(tzinfo=utc))
    def test_academic_programs_absences_second_semester(self, mocked_method):
        self.client.login(username=self.principal.username, password='passwd')
        AcademicProgramFactory(unfounded_abs_avg_sem1=1, unfounded_abs_avg_annual=1, school_unit=self.school_unit)
        AcademicProgramFactory(unfounded_abs_avg_sem1=2, unfounded_abs_avg_annual=2, school_unit=self.school_unit)
        AcademicProgramFactory(unfounded_abs_avg_sem1=3, unfounded_abs_avg_annual=3, school_unit=self.school_unit)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        for result in response.data['results']:
            self.assertCountEqual(result.keys(), self.expected_fields)
        self.assertEqual(response.data['results'][0]['unfounded_abs_avg_annual'], 3)
        self.assertEqual(response.data['results'][1]['unfounded_abs_avg_annual'], 2)
        self.assertEqual(response.data['results'][2]['unfounded_abs_avg_annual'], 1)
