from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.academic_programs.factories import GenericAcademicProgramFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory
from edualert.subjects.factories import SubjectFactory, ProgramSubjectThroughFactory


@ddt
class GenericAcademicProgramDetailTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.program = GenericAcademicProgramFactory(optional_subjects_weekly_hours={
            "IX": 10,
            "X": 1
        })

    @staticmethod
    def build_url(program_id):
        return reverse('academic_programs:generic-academic-program-detail', kwargs={'id': program_id})

    def test_generic_academic_program_detail_unauthenticated(self):
        response = self.client.get(self.build_url(self.program.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_generic_academic_program_detail_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.build_url(self.program.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_generic_academic_program_detail(self):
        self.client.login(username=self.principal.username, password='passwd')

        subject1 = SubjectFactory(name='Subject B')
        subject2 = SubjectFactory(name='Subject C')
        subject3 = SubjectFactory(name='Subject A')
        subject_through1 = ProgramSubjectThroughFactory(generic_academic_program=self.program, subject=subject1)
        subject_through2 = ProgramSubjectThroughFactory(generic_academic_program=self.program, subject=subject2,
                                                        class_grade='X', class_grade_arabic=10)
        subject_through3 = ProgramSubjectThroughFactory(generic_academic_program=self.program, subject=subject3)

        response = self.client.get(self.build_url(self.program.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data.keys(), ['id', 'subjects', 'optional_subjects_weekly_hours'])

        subjects_response = response.data['subjects']
        self.assertEqual(len(subjects_response.keys()), 2)
        self.assertTrue(all(['IX' in subjects_response.keys(), 'X' in subjects_response.keys()]))
        self.assertEqual([subject_through['id'] for subject_through in subjects_response['IX']],
                         [subject_through3.id, subject_through1.id])
        self.assertEqual([subject_through['id'] for subject_through in subjects_response['X']],
                         [subject_through2.id, ])
