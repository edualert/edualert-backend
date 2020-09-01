from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.academic_programs.factories import AcademicProgramFactory, GenericAcademicProgramFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class AcademicProgramDetailTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.optional_subjects_weekly_hours = {
            'IX': 10,
            'X': 8,
            'XI': 6,
            'XII': 6
        }
        cls.generic_academic_program = GenericAcademicProgramFactory(optional_subjects_weekly_hours=cls.optional_subjects_weekly_hours)
        cls.academic_program = AcademicProgramFactory(generic_academic_program=cls.generic_academic_program, school_unit=cls.school_unit)

    @staticmethod
    def build_url(program_id):
        return reverse('academic_programs:academic-program-detail', kwargs={'id': program_id})

    def test_academic_program_detail_unauthenticated(self):
        response = self.client.get(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_academic_program_detail_wrong_user_type(self, user_role):
        user_profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )

        self.client.login(username=user_profile.username, password='passwd')
        response = self.client.get(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_academic_program_detail_expected_fields(self):
        self.client.login(username=self.principal.username, password='passwd')

        expected_fields = ['id', 'name', 'classes_count', 'academic_year', 'core_subject', 'optional_subjects_weekly_hours', 'subjects']
        subjects_expected_fields = ['mandatory_subjects', 'optional_subjects']
        subject_expected_fields = ['subject_id', 'subject_name', 'id', 'weekly_hours_count']

        subject1 = SubjectFactory(name='Subject A')
        ProgramSubjectThroughFactory(class_grade='X', academic_program=self.academic_program,
                                     subject=subject1, is_mandatory=False, class_grade_arabic=10)
        subject2 = SubjectFactory(name='Subject B')
        ProgramSubjectThroughFactory(academic_program=self.academic_program, subject=subject2,
                                     class_grade='X', is_mandatory=True, class_grade_arabic=10)

        response = self.client.get(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertCountEqual(response.data.keys(), expected_fields)
        self.assertEqual(len(response.data['subjects']), 1)
        self.assertCountEqual(response.data['subjects']['X'].keys(), subjects_expected_fields)
        for subject in response.data['subjects']['X']['optional_subjects']:
            self.assertCountEqual(subject.keys(), subject_expected_fields)
        for subject in response.data['subjects']['X']['mandatory_subjects']:
            self.assertCountEqual(subject.keys(), subject_expected_fields)

    def test_academic_program_detail(self):
        self.client.login(username=self.principal.username, password='passwd')

        subject1 = SubjectFactory(name='Subject A')
        subject2 = SubjectFactory(name='Subject C')
        subject3 = SubjectFactory(name='Subject B')
        subject_through1 = ProgramSubjectThroughFactory(
            academic_program=self.academic_program,
            subject=subject1, is_mandatory=False,
            class_grade='IX', class_grade_arabic=9
        )
        subject_through2 = ProgramSubjectThroughFactory(
            academic_program=self.academic_program,
            subject=subject2, class_grade='X', class_grade_arabic=10,
            is_mandatory=False
        )
        subject_through3 = ProgramSubjectThroughFactory(
            generic_academic_program=self.generic_academic_program,
            subject=subject3, is_mandatory=True,
            class_grade='IX', class_grade_arabic=9
        )

        response = self.client.get(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['optional_subjects_weekly_hours'], self.optional_subjects_weekly_hours)

        subjects = response.data['subjects']
        self.assertCountEqual(subjects.keys(), ['IX', 'X'])
        self.assertEqual(subjects['IX']['optional_subjects'][0]['id'], subject_through1.id)
        self.assertEqual(subjects['X']['optional_subjects'][0]['id'], subject_through2.id)
        self.assertEqual(subjects['IX']['mandatory_subjects'][0]['id'], subject_through3.id)

