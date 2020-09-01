from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.academic_programs.factories import GenericAcademicProgramFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitProfileFactory


@ddt
class GenericAcademicProgramListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserProfileFactory(user_role=UserProfile.UserRoles.ADMINISTRATOR)
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.academic_profile = SchoolUnitProfileFactory()
        cls.category = cls.academic_profile.category
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal, academic_profile=cls.academic_profile)
        cls.school_unit.categories.add(cls.category)
        cls.teacher = UserProfileFactory(user_role=UserProfile.UserRoles.TEACHER, school_unit=cls.school_unit)

        cls.program1 = GenericAcademicProgramFactory(name='Program D', category=cls.category, academic_profile=cls.academic_profile)
        cls.program2 = GenericAcademicProgramFactory(name='Program B', category=cls.category)
        cls.program3 = GenericAcademicProgramFactory(name='Program A', academic_profile=cls.academic_profile)
        cls.program4 = GenericAcademicProgramFactory(name='Program C', category=cls.category, academic_profile=cls.academic_profile)
        cls.program5 = GenericAcademicProgramFactory(name='Program E')

        cls.url = reverse('academic_programs:generic-academic-program-list')

    def test_unregistered_academic_program_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_generic_academic_program_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(user_role=user_role, school_unit=self.school_unit)
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_generic_academic_program_list_admin(self):
        self.client.login(username=self.admin.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        for response_program, program in zip(response.data, [self.program3, self.program2, self.program4,
                                                             self.program1, self.program5]):
            self.assertEqual(response_program['id'], program.id)
            self.assertCountEqual(response_program.keys(), ['id', 'name'])

        # Search by name
        response = self.client.get(self.url, {'search': 'Program B'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.program2.id)

    @data(
        'principal', 'teacher'
    )
    def test_generic_academic_program_list_school_employee(self, user_param):
        self.client.login(username=getattr(self, user_param).username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for response_program, program in zip(response.data, [self.program4, self.program1]):
            self.assertEqual(response_program['id'], program.id)
            self.assertCountEqual(response_program.keys(), ['id', 'name'])

        # Search by name
        response = self.client.get(self.url, {'search': 'Program D'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.program1.id)
