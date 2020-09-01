from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.catalogs.factories import StudentCatalogPerSubjectFactory, StudentCatalogPerYearFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitProfileFactory
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import ProgramSubjectThroughFactory


@ddt
class OwnSchoolSituationTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.school_unit = RegisteredSchoolUnitFactory(academic_profile=SchoolUnitProfileFactory(name='Sportiv'))
        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, class_grade='IX', class_grade_arabic=9)
        cls.student = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, school_unit=cls.school_unit, student_in_class=cls.study_class)

        StudentCatalogPerYearFactory(student=cls.student, study_class=cls.study_class)
        cls.student_catalog_per_subject = StudentCatalogPerSubjectFactory(
            student=cls.student,
            study_class=cls.study_class
        )
        ProgramSubjectThroughFactory(academic_program=cls.study_class.academic_program, class_grade=cls.study_class.class_grade,
                                     subject=cls.student_catalog_per_subject.subject, weekly_hours_count=2)

        cls.url = reverse('statistics:own-school-situation')

    def test_own_school_situation_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.PRINCIPAL,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT
    )
    def test_own_school_situation_wrong_user_type(self, user_role):
        user = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_own_school_situation_success(self):
        self.client.login(username=self.student.username, password='passwd')
        another_catalog = StudentCatalogPerSubjectFactory(
            student=self.student,
            study_class=self.study_class,
            academic_year=self.calendar.academic_year
        )
        ProgramSubjectThroughFactory(academic_program=self.study_class.academic_program, class_grade=self.study_class.class_grade,
                                     subject=another_catalog.subject, weekly_hours_count=2)
        StudentCatalogPerSubjectFactory(student=self.student, academic_year=self.calendar.academic_year - 1)

        expected_fields = ['id', 'full_name', 'study_class', 'labels', 'risk_description', 'catalogs_per_subjects']
        expected_study_class_fields = ['id', 'class_grade', 'class_letter', 'academic_program_name', 'class_master']
        expected_class_master_fields = ['id', 'full_name']
        expected_catalog_fields = [
            'id', 'subject_name', 'teacher', 'avg_sem1', 'avg_sem2', 'avg_annual', 'avg_after_2nd_examination', 'avg_limit',
            'grades_sem1', 'grades_sem2', 'second_examination_grades', 'difference_grades_sem1', 'difference_grades_sem2',
            'abs_count_sem1', 'abs_count_sem2', 'abs_count_annual',
            'founded_abs_count_sem1', 'founded_abs_count_sem2', 'founded_abs_count_annual',
            'unfounded_abs_count_sem1', 'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
            'third_of_hours_count_sem1', 'third_of_hours_count_sem2', 'third_of_hours_count_annual',
            'abs_sem1', 'abs_sem2', 'wants_thesis', 'is_exempted', 'is_coordination_subject'
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertCountEqual(response.data['study_class'].keys(), expected_study_class_fields)
        self.assertCountEqual(response.data['study_class']['class_master'].keys(), expected_class_master_fields)
        self.assertEqual(len(response.data['catalogs_per_subjects']), 2)

        for catalog in response.data['catalogs_per_subjects']:
            self.assertCountEqual(catalog.keys(), expected_catalog_fields)
            self.assertEqual(catalog['avg_limit'], 5)
            self.assertEqual(catalog['third_of_hours_count_sem1'], 10)
            self.assertEqual(catalog['third_of_hours_count_sem2'], 10)
            self.assertEqual(catalog['third_of_hours_count_annual'], 20)

    def test_own_school_situation_filter_by_academic_year(self):
        self.client.login(username=self.student.username, password='passwd')

        StudentCatalogPerSubjectFactory(
            student=self.student,
            academic_year=self.calendar.academic_year
        )
        past_study_class = StudyClassFactory(school_unit=self.school_unit, class_grade='IX', class_grade_arabic=9,
                                             academic_year=self.calendar.academic_year - 1)
        StudentCatalogPerYearFactory(student=self.student, study_class=past_study_class)
        past_catalog = StudentCatalogPerSubjectFactory(
            student=self.student,
            study_class=past_study_class,
            academic_year=self.calendar.academic_year - 1
        )
        ProgramSubjectThroughFactory(academic_program=past_study_class.academic_program, class_grade=past_study_class.class_grade,
                                     subject=past_catalog.subject, weekly_hours_count=3)
        past_study_class.academic_program.core_subject = past_catalog.subject
        past_study_class.academic_program.save()

        response = self.client.get(self.url, {'academic_year': self.calendar.academic_year - 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['study_class']['class_grade'], 'IX')
        self.assertEqual(response.data['study_class']['academic_program_name'], past_study_class.academic_program_name)
        self.assertEqual(len(response.data['catalogs_per_subjects']), 1)
        self.assertEqual(response.data['catalogs_per_subjects'][0]['id'], past_catalog.id)
        self.assertEqual(response.data['catalogs_per_subjects'][0]['avg_limit'], 6)
        self.assertEqual(response.data['catalogs_per_subjects'][0]['third_of_hours_count_sem1'], 15)
        self.assertEqual(response.data['catalogs_per_subjects'][0]['third_of_hours_count_sem2'], 15)
        self.assertEqual(response.data['catalogs_per_subjects'][0]['third_of_hours_count_annual'], 30)
