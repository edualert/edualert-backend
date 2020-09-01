from ddt import data, ddt
from django.urls import reverse
from rest_framework import status

from edualert.academic_programs.factories import AcademicProgramFactory, GenericAcademicProgramFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitCategoryFactory


@ddt
class AcademicProgramListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal)
        cls.academic_year = 2020

    @staticmethod
    def build_url(academic_year):
        return reverse('academic_programs:academic-program-list', kwargs={'academic_year': academic_year})

    def test_academic_program_list_unauthenticated(self):
        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR, UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.PARENT, UserProfile.UserRoles.STUDENT
    )
    def test_academic_program_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')
        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_academic_program_list_no_data(self):
        self.client.login(username=self.principal.username, password='passwd')
        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_academic_program_list_success(self):
        self.client.login(username=self.principal.username, password='passwd')

        academic_program = AcademicProgramFactory(academic_year=self.academic_year, school_unit=self.school_unit)
        academic_program2 = AcademicProgramFactory(academic_year=self.academic_year, school_unit=self.school_unit)
        AcademicProgramFactory(academic_year=self.academic_year, school_unit=RegisteredSchoolUnitFactory())
        AcademicProgramFactory(academic_year=2000, school_unit=self.school_unit)

        response = self.client.get(self.build_url(self.academic_year))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['count'], 2)

        for program in response.data['results']:
            self.assertIn(program['id'], [academic_program.id, academic_program2.id])

    def test_academic_program_list_search(self):
        self.client.login(username=self.principal.username, password='passwd')

        academic_program = AcademicProgramFactory(academic_year=self.academic_year, name='program', school_unit=self.school_unit)
        AcademicProgramFactory(academic_year=self.academic_year, name='other', school_unit=self.school_unit)
        AcademicProgramFactory(
            academic_year=self.academic_year, name='program', school_unit=RegisteredSchoolUnitFactory()
        )

        response = self.client.get(self.build_url(self.academic_year), {'search': 'program'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], academic_program.id)

    def test_academic_program_list_filter_by_category(self):
        self.client.login(username=self.principal.username, password='passwd')
        highschool_category = SchoolUnitCategoryFactory()
        self.school_unit.categories.add(highschool_category)

        AcademicProgramFactory(academic_year=self.academic_year, name='program',  school_unit=self.school_unit,
                               generic_academic_program=GenericAcademicProgramFactory(category=highschool_category))
        AcademicProgramFactory(academic_year=self.academic_year, name='other', school_unit=self.school_unit,
                               generic_academic_program=GenericAcademicProgramFactory(category=highschool_category))

        response = self.client.get(self.build_url(self.academic_year), {'class_grade': 'IX'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        response = self.client.get(self.build_url(self.academic_year), {'class_grade': 'IV'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
