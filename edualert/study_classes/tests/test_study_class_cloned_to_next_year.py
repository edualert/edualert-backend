from ddt import ddt, data, unpack
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.catalogs.factories import StudentCatalogPerYearFactory, StudentCatalogPerSubjectFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.study_classes.factories import StudyClassFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class StudyClassClonedToNextYearTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.calendar = AcademicYearCalendarFactory()
        cls.last_year = cls.calendar.academic_year - 1

        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)

        cls.last_year_program = AcademicProgramFactory(school_unit=cls.school_unit, academic_year=cls.last_year)
        cls.current_year_program = AcademicProgramFactory(school_unit=cls.school_unit, name=cls.last_year_program.name, academic_year=cls.last_year + 1)

        cls.study_class = StudyClassFactory(school_unit=cls.school_unit, academic_program=cls.last_year_program, academic_year=cls.last_year)

    @staticmethod
    def build_url(study_class_id):
        return reverse('study_classes:study-class-cloned-to-next-year', kwargs={'id': study_class_id})

    def test_study_class_cloned_to_next_year_unauthenticated(self):
        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_study_class_cloned_to_next_year_wrong_user_type(self, user_role):
        if user_role == UserProfile.UserRoles.ADMINISTRATOR:
            user = UserProfileFactory(user_role=user_role)
        else:
            user = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=user.username, password='passwd')

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_study_class_cloned_to_next_year_not_found(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.get(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_study_class_cloned_to_next_year_not_last_year(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.get(self.build_url(StudyClassFactory(school_unit=self.school_unit).id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'Can only clone study classes from previous academic year.')

    @data(
        ('IV', 4),
        ('VIII', 8),
        ('XII', 12),
        ('XIII', 13),
    )
    @unpack
    def test_study_class_cloned_to_next_year_wrong_class_grade(self, class_grade, class_grade_arabic):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.get(self.build_url(StudyClassFactory(school_unit=self.school_unit, academic_year=self.last_year,
                                                                    class_grade=class_grade, class_grade_arabic=class_grade_arabic).id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'This study class cannot be cloned.')

    def test_study_class_cloned_to_next_year_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        subject1 = SubjectFactory(name='Subject B')
        subject2 = SubjectFactory(name='Subject C')
        subject3 = SubjectFactory(name='Subject A')
        ProgramSubjectThroughFactory(subject=subject1, academic_program=self.current_year_program, class_grade='VII', class_grade_arabic=7, is_mandatory=False)
        ProgramSubjectThroughFactory(subject=subject2, academic_program=self.current_year_program, class_grade='VII', class_grade_arabic=7, is_mandatory=False)
        ProgramSubjectThroughFactory(subject=subject3, generic_academic_program=self.current_year_program.generic_academic_program,
                                     class_grade='VII', class_grade_arabic=7)

        student1 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student B', student_in_class=self.study_class)
        StudentCatalogPerYearFactory(student=student1, study_class=self.study_class)

        # Behavior grade below 6
        student2 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student C', student_in_class=self.study_class)
        StudentCatalogPerYearFactory(student=student2, study_class=self.study_class, behavior_grade_annual=5)

        student3 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student A', student_in_class=self.study_class)
        StudentCatalogPerYearFactory(student=student3, study_class=self.study_class)

        # No average
        student4 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student E', student_in_class=self.study_class)
        StudentCatalogPerYearFactory(student=student4, study_class=self.study_class)
        StudentCatalogPerSubjectFactory(student=student4, subject=subject1, study_class=self.study_class)

        # Average below 5
        student5 = UserProfileFactory(user_role=UserProfile.UserRoles.STUDENT, full_name='Student D', student_in_class=self.study_class)
        StudentCatalogPerYearFactory(student=student5, study_class=self.study_class)
        StudentCatalogPerSubjectFactory(student=student5, subject=subject2, study_class=self.study_class, avg_final=4)

        response = self.client.get(self.build_url(self.study_class.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertCountEqual(response.data.keys(), ['class_grade', 'class_letter', 'academic_program', 'academic_program_name',
                                                     'class_master', 'subjects', 'students'])
        self.assertCountEqual(response.data['class_master'].keys(), ['id', 'full_name'])
        for subject in response.data['subjects']:
            self.assertCountEqual(subject.keys(), ['subject_id', 'subject_name', 'is_mandatory'])
        for subject in response.data['students']:
            self.assertCountEqual(subject.keys(), ['id', 'full_name'])

        self.assertEqual(response.data['class_grade'], 'VII')
        self.assertEqual(response.data['class_letter'], 'A')
        self.assertEqual(response.data['academic_program'], self.current_year_program.id)
        self.assertEqual(response.data['academic_program_name'], self.current_year_program.name)
        self.assertEqual(response.data['class_master']['id'], self.study_class.class_master_id)

        subjects_response = response.data['subjects']
        self.assertEqual(len(subjects_response), 3)
        self.assertEqual(subjects_response[0]['subject_id'], subject3.id)
        self.assertTrue(subjects_response[0]['is_mandatory'])
        self.assertEqual(subjects_response[1]['subject_id'], subject1.id)
        self.assertFalse(subjects_response[1]['is_mandatory'])
        self.assertEqual(subjects_response[2]['subject_id'], subject2.id)
        self.assertFalse(subjects_response[2]['is_mandatory'])

        students_response = response.data['students']
        self.assertEqual(len(students_response), 2)
        self.assertEqual(students_response[0]['id'], student3.id)
        self.assertEqual(students_response[1]['id'], student1.id)
