from ddt import ddt, data
from django.urls import reverse
from rest_framework import status

from edualert.academic_calendars.factories import AcademicYearCalendarFactory
from edualert.academic_programs.factories import GenericAcademicProgramFactory, AcademicProgramFactory
from edualert.common.api_tests import CommonAPITestCase
from edualert.profiles.factories import UserProfileFactory
from edualert.profiles.models import UserProfile
from edualert.schools.factories import RegisteredSchoolUnitFactory, SchoolUnitProfileFactory


@ddt
class UnregisteredAcademicProgramListTestCase(CommonAPITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.principal = UserProfileFactory(user_role=UserProfile.UserRoles.PRINCIPAL)
        cls.academic_profile = SchoolUnitProfileFactory()
        cls.category = cls.academic_profile.category
        cls.school_unit = RegisteredSchoolUnitFactory(school_principal=cls.principal, academic_profile=cls.academic_profile)
        cls.school_unit.categories.add(cls.category)
        cls.url = reverse('academic_programs:unregistered-academic-program-list')

    def test_unregistered_academic_program_list_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @data(
        UserProfile.UserRoles.ADMINISTRATOR,
        UserProfile.UserRoles.TEACHER,
        UserProfile.UserRoles.STUDENT,
        UserProfile.UserRoles.PARENT
    )
    def test_unregistered_academic_program_list_wrong_user_type(self, user_role):
        profile = UserProfileFactory(
            user_role=user_role,
            school_unit=self.school_unit if user_role != UserProfile.UserRoles.ADMINISTRATOR else None
        )
        self.client.login(username=profile.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unregistered_academic_program_list_no_calendar(self):
        self.client.login(username=self.principal.username, password='passwd')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_unregistered_academic_program_list(self):
        self.client.login(username=self.principal.username, password='passwd')

        AcademicYearCalendarFactory()

        generic_program1 = GenericAcademicProgramFactory(name='Program B', category=self.category, academic_profile=self.academic_profile)
        generic_program2 = GenericAcademicProgramFactory(name='Program A', category=self.category, academic_profile=self.academic_profile)
        generic_program3 = GenericAcademicProgramFactory(name='Program C', category=self.category, academic_profile=self.academic_profile)
        GenericAcademicProgramFactory(name='Program D')
        AcademicProgramFactory(school_unit=self.school_unit, generic_academic_program=generic_program3)
        AcademicProgramFactory(school_unit=self.school_unit, generic_academic_program=generic_program2, academic_year=2018)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], generic_program2.id)
        self.assertEqual(response.data[1]['id'], generic_program1.id)

        # Search by name
        response = self.client.get(self.url, {'search': 'Program B'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], generic_program1.id)
        self.assertCountEqual(response.data[0].keys(), ['id', 'name'])
