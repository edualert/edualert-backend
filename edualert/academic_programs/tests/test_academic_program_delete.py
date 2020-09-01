from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_programs.factories import AcademicProgramFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory


@ddt
class AcademicProgramDeleteTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.academic_program = AcademicProgramFactory(school_unit=cls.school_unit)

    @staticmethod
    def build_url(program_id):
        return reverse('academic_programs:academic-program-detail', kwargs={'id': program_id})

    def test_delete_academic_program_unauthenticated(self):
        response = self.client.delete(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_delete_academic_program_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.delete(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_academic_program_not_found(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.delete(self.build_url(0))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_academic_program_different_school(self):
        profile = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        RegisteredSchoolUnitFactory(school_principal=profile)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.delete(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_academic_program_with_classes(self):
        self.client.login(username=self.principal.username, password='passwd')
        self.academic_program.classes_count = 1
        self.academic_program.save()

        response = self.client.delete(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], "Cannot delete an academic program that still has study classes assigned.")

    def test_delete_academic_program_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.delete(self.build_url(self.academic_program.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
