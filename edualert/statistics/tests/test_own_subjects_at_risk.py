from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitProfileFactory
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import ProgramSubjectThroughFactory, SubjectFactory


@ddt
class OwnSubjectsAtRiskTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory(academic_profile=SchoolUnitProfileFactory(name='Militar'))
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_grade='IX', class_grade_arabic=9)

        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class)
        cls.url = reverse('statistics:own-subjects-at-risk')

    def test_own_subjects_at_risk_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT
    )
    def test_own_subjects_at_risk_wrong_user_type(self, user_role):
        user = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_subjects_at_risk_success(self):
        self.client.login(username=self.student.username, password='passwd')

        subject1 = SubjectFactory(name='B')
        catalog1 = StudentCatalogPerSubjectFactory(
            student=self.student,
            subject=subject1,
            study_class=self.study_class,
            is_at_risk=True,
            unfounded_abs_count_sem1=1,
            unfounded_abs_count_annual=1,
        )
        ProgramSubjectThroughFactory(academic_program=self.study_class.academic_program, class_grade=self.study_class.class_grade,
                                     subject=subject1, weekly_hours_count=5)

        subject2 = SubjectFactory(name='A', is_coordination=True)
        catalog2 = StudentCatalogPerSubjectFactory(
            student=self.student,
            subject=subject2,
            is_coordination_subject=True,
            study_class=self.study_class,
            is_at_risk=True,
            unfounded_abs_count_sem1=2,
            unfounded_abs_count_annual=2
        )
        ProgramSubjectThroughFactory(academic_program=self.study_class.academic_program, class_grade=self.study_class.class_grade,
                                     subject=subject2, weekly_hours_count=1)

        StudentCatalogPerSubjectFactory(
            student=self.student,
            study_class=self.study_class,
            is_at_risk=False
        )

        expected_fields = ['id', 'subject_name', 'avg_sem1', 'avg_final', 'avg_limit',
                           'unfounded_abs_count_sem1', 'unfounded_abs_count_annual',
                           'third_of_hours_count_sem1', 'third_of_hours_count_annual']

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        for catalog in response.data['results']:
            self.assertCountEqual(catalog.keys(), expected_fields)

        self.assertEqual(response.data['results'][0]['id'], catalog2.id)
        self.assertEqual(response.data['results'][0]['avg_limit'], 8)
        self.assertEqual(response.data['results'][0]['third_of_hours_count_sem1'], 5)
        self.assertEqual(response.data['results'][0]['third_of_hours_count_annual'], 10)

        self.assertEqual(response.data['results'][1]['id'], catalog1.id)
        self.assertEqual(response.data['results'][1]['avg_limit'], 5)
        self.assertEqual(response.data['results'][1]['third_of_hours_count_sem1'], 25)
        self.assertEqual(response.data['results'][1]['third_of_hours_count_annual'], 50)
