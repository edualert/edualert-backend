from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerYearFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class SchoolStudentsAtRiskTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.url = reverse('statistics:school-students-at-risk')

    def test_school_students_at_risk_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT,
        UserProfile.UserRoles.STUDENT
    )
    def test_school_students_at_risk_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_school_students_at_risk_no_calendar(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.calendar.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_school_students_at_risk_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        catalog1 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT,
                                                                           school_unit=self.school_unit, is_at_risk=True, full_name='b'),
                                                unfounded_abs_count_sem1=2, unfounded_abs_count_annual=2)
        catalog2 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT,
                                                                           school_unit=self.school_unit, is_at_risk=True, full_name='c'),
                                                unfounded_abs_count_sem1=1, unfounded_abs_count_annual=1)
        catalog3 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT,
                                                                           school_unit=self.school_unit, is_at_risk=True, full_name='e'),
                                                unfounded_abs_count_sem1=3, unfounded_abs_count_annual=3,
                                                behavior_grade_sem1=8, behavior_grade_annual=8)
        catalog4 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT,
                                                                           school_unit=self.school_unit, is_at_risk=True, full_name='d'),
                                                unfounded_abs_count_sem1=3, unfounded_abs_count_annual=3,
                                                behavior_grade_sem1=9, behavior_grade_annual=9)
        catalog5 = StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT,
                                                                           school_unit=self.school_unit, is_at_risk=True, full_name='a'),
                                                unfounded_abs_count_sem1=2, unfounded_abs_count_annual=2)
        StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=self.school_unit))
        StudentCatalogPerYearFactory(student=UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, is_at_risk=True))

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

        expected_fields = ['id', 'student', 'avg_sem1', 'avg_final', 'unfounded_abs_count_sem1', 'unfounded_abs_count_annual',
                           'second_examinations_count', 'behavior_grade_sem1', 'behavior_grade_annual', 'behavior_grade_limit',
                           'study_class']
        expected_student_fields = ['id', 'full_name']
        expected_study_class_fields = ['id', 'class_grade', 'class_letter']
        for result in response.data['results']:
            self.assertCountEqual(result.keys(), expected_fields)
            self.assertCountEqual(result['student'].keys(), expected_student_fields)
            self.assertCountEqual(result['study_class'].keys(), expected_study_class_fields)

        self.assertEqual(response.data['results'][0]['id'], catalog4.id)
        self.assertEqual(response.data['results'][1]['id'], catalog3.id)
        self.assertEqual(response.data['results'][2]['id'], catalog5.id)
        self.assertEqual(response.data['results'][3]['id'], catalog1.id)
        self.assertEqual(response.data['results'][4]['id'], catalog2.id)
