from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class AcademicProgramsAtRiskTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.calendar = AcademicYearCalendarFactory()
        cls.url = reverse('statistics:programs-at-risk')

    def test_academic_programs_at_risk_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_academic_programs_at_risk_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_academic_programs_at_risk_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        academic_program1 = AcademicProgramFactory(students_at_risk_count=2, school_unit=self.school_unit)
        academic_program2 = AcademicProgramFactory(students_at_risk_count=1, school_unit=self.school_unit)
        academic_program3 = AcademicProgramFactory(students_at_risk_count=3, name='a', school_unit=self.school_unit)
        academic_program4 = AcademicProgramFactory(students_at_risk_count=3, name='b', school_unit=self.school_unit)
        AcademicProgramFactory(students_at_risk_count=0, school_unit=self.school_unit)
        AcademicProgramFactory(students_at_risk_count=1, academic_year=2018, school_unit=self.school_unit)
        AcademicProgramFactory(students_at_risk_count=1)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)
        for result in response.data['results']:
            self.assertCountEqual(result.keys(), ['id', 'name', 'students_at_risk_count'])
        self.assertEqual(response.data['results'][0]['id'], academic_program3.id)
        self.assertEqual(response.data['results'][1]['id'], academic_program4.id)
        self.assertEqual(response.data['results'][2]['id'], academic_program1.id)
        self.assertEqual(response.data['results'][3]['id'], academic_program2.id)
