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
class AcademicProgramSubjectListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.generic_academic_program = GenericAcademicProgramFactory()
        cls.academic_program = AcademicProgramFactory(school_unit=cls.school_unit, generic_academic_program=cls.generic_academic_program)
        cls.mandatory_subject = SubjectFactory(name='Mandatory')
        cls.optional_subject = SubjectFactory(name='Optional')
        cls.mandatory_through = ProgramSubjectThroughFactory(
            generic_academic_program=cls.generic_academic_program, subject=cls.mandatory_subject,
            class_grade='IX', class_grade_arabic=9
        )
        cls.optional_through = ProgramSubjectThroughFactory(
            academic_program=cls.academic_program, subject=cls.optional_subject,
            class_grade='IX', class_grade_arabic=9, is_mandatory=False
        )

    @staticmethod
    def build_url(program_id):
        return reverse('academic_programs:academic-program-subject-list', kwargs={'id': program_id})

    def get_response(self):
        return self.client.get(self.build_url(self.academic_program.id), {'grade': 'IX'})

    def test_academic_program_subject_list_unauthenticated(self):
        response = self.client.get(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_academic_program_subject_list_wrong_user_type(self, user_role):
        user_profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )

        self.client.login(username=user_profile.username, password='passwd')
        response = self.client.get(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_academic_program_subject_list_inexistent_academic_year(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.get(self.build_url(0), {'grade': 'IX'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_academic_program_subject_list_missing_class_grade(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.get(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'class_grade': ['grade query param is missing.']})

    def test_academic_program_subject_list_expected_fields(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.get_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        expected_fields = ['subject_id', 'subject_name', 'is_mandatory']

        for subject in response.data:
            self.assertCountEqual(subject.keys(), expected_fields)

    def test_academic_program_subject_list_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        # Create a subject through with another class grade
        subject = SubjectFactory(name='Wrong class grade')
        ProgramSubjectThroughFactory(
            generic_academic_program=self.generic_academic_program, subject=subject,
            class_grade='X', class_grade_arabic=10
        )

        response = self.get_response()
        self.assertEqual(len(response.data), 2)
        self.assertCountEqual([subject['subject_id'] for subject in response.data], [self.optional_subject.id, self.mandatory_subject.id])
        self.assertCountEqual([subject['is_mandatory'] for subject in response.data], [False, True])

        # Create a mandatory subject from another generic academic program
        generic_academic_program = GenericAcademicProgramFactory()
        subject = SubjectFactory(name='Other generic academic program')
        ProgramSubjectThroughFactory(
            generic_academic_program=generic_academic_program, subject=subject,
            class_grade='IX', class_grade_arabic=9
        )
        response = self.get_response()
        self.assertEqual(len(response.data), 2)
        
        # Create another optional subject
        subject = SubjectFactory(name='Other optional')
        ProgramSubjectThroughFactory(
            academic_program=self.academic_program, subject=subject,
            class_grade='IX', class_grade_arabic=9, is_mandatory=False
        )
        response = self.get_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # Create another mandatory subject
        subject = SubjectFactory(name='Other mandatory')
        ProgramSubjectThroughFactory(
            generic_academic_program=self.generic_academic_program, subject=subject,
            class_grade='IX', class_grade_arabic=9
        )
        response = self.get_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
